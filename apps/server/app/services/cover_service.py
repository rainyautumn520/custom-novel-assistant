import base64

import httpx
from sqlalchemy import select

from app.config import settings
from app.core.database import new_id, project_db_path, project_session
from app.models.ai import CoverTask


def list_tasks(project_id: str) -> list[CoverTask]:
    with project_session(project_id) as session:
        return list(session.scalars(select(CoverTask).order_by(CoverTask.created_at.desc())))


def get_task_or_404(project_id: str, task_id: str) -> CoverTask:
    from fastapi import HTTPException

    with project_session(project_id) as session:
        task = session.get(CoverTask, task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="任务不存在")
        return task


def create_task(project_id: str, prompt: str, params: dict) -> CoverTask:
    """创建并同步执行封面生成任务（真实调用 Seedream 5.0）。"""
    task = CoverTask(
        id=new_id(),
        prompt=prompt,
        params=params,
        idempotency_key=new_id(),
        status="queued",
    )
    if not settings.seedream_api_key:
        task.status = "failed"
        task.error = "凭证未配置（AI_NOVEL_SEEDREAM_API_KEY），封面生成待联调启用"
        with project_session(project_id) as session:
            session.add(task)
            session.commit()
            session.refresh(task)
            return task

    _run_generation(project_id, task, prompt, params)
    with project_session(project_id) as session:
        session.add(task)
        session.commit()
        session.refresh(task)
        return task


def _run_generation(project_id: str, task: CoverTask, prompt: str, params: dict) -> None:
    """调用火山方舟 /images/generations，结果以 b64_json 或 url 保存到作品目录。"""
    try:
        resp = httpx.post(
            f"{settings.seedream_base_url.rstrip('/')}/images/generations",
            headers={"Authorization": f"Bearer {settings.seedream_api_key}"},
            json={
                "model": settings.seedream_model,
                "prompt": prompt,
                "size": params.get("size", "1920x1920"),
                "response_format": "b64_json",
            },
            timeout=180,
        )
        resp.raise_for_status()
        data = resp.json()["data"][0]
        covers_dir = project_db_path(project_id).parent / "covers"
        covers_dir.mkdir(parents=True, exist_ok=True)
        target = covers_dir / f"{task.id}.png"
        if data.get("b64_json"):
            target.write_bytes(base64.b64decode(data["b64_json"]))
        elif data.get("url"):
            img = httpx.get(data["url"], timeout=90)
            img.raise_for_status()
            target.write_bytes(img.content)
        else:
            raise RuntimeError("响应中既无 b64_json 也无 url")
        task.status = "success"
        task.result_path = f"covers/{task.id}.png"
        task.optimized_prompt = prompt
    except httpx.HTTPStatusError as exc:
        task.status = "failed"
        try:
            detail = exc.response.json().get("error", {}).get("message") or exc.response.text
        except Exception:
            detail = exc.response.text[:300]
        task.error = f"生成失败（{exc.response.status_code}）：{detail}"
    except Exception as exc:  # 网络/超时/解析错误
        task.status = "failed"
        task.error = f"生成失败：{exc}"
