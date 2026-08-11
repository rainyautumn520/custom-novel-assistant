from sqlalchemy import select

from app.config import settings
from app.core.database import new_id, project_session
from app.models.ai import CoverTask


def list_tasks(project_id: str) -> list[CoverTask]:
    with project_session(project_id) as session:
        return list(session.scalars(select(CoverTask).order_by(CoverTask.created_at.desc())))


def create_task(project_id: str, prompt: str, params: dict) -> CoverTask:
    """创建封面生成任务。

    骨架阶段只登记任务与状态，不发起真实调用：模型标识与鉴权以官方文档为准
    （ADR-05），联调前统一标记为 failed 并给出配置提示。
    """
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
