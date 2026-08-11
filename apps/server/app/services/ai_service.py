import httpx
from sqlalchemy import select

from app.config import settings
from app.core.database import new_id, project_session
from app.models.ai import AiMessage, AiSession, ProjectSetting
from app.models.world import Setting


def list_sessions(project_id: str) -> list[AiSession]:
    with project_session(project_id) as session:
        return list(session.scalars(select(AiSession).order_by(AiSession.updated_at.desc())))


def create_session(project_id: str, title: str = "新讨论") -> AiSession:
    with project_session(project_id) as session:
        ai_session = AiSession(title=title)
        session.add(ai_session)
        session.commit()
        session.refresh(ai_session)
        return ai_session


def delete_session(project_id: str, session_id: str) -> None:
    from fastapi import HTTPException

    with project_session(project_id) as session:
        ai_session = session.get(AiSession, session_id)
        if ai_session is None:
            raise HTTPException(status_code=404, detail="会话不存在")
        session.delete(ai_session)
        session.commit()


def list_messages(project_id: str, session_id: str) -> list[AiMessage]:
    with project_session(project_id) as session:
        if session.get(AiSession, session_id) is None:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="会话不存在")
        return list(
            session.scalars(
                select(AiMessage)
                .where(AiMessage.session_id == session_id)
                .order_by(AiMessage.created_at)
            )
        )


def _build_context(project_id: str, session_id: str, user_content: str) -> tuple[str, list[dict]]:
    with project_session(project_id) as session:
        confirmed = session.scalars(
            select(Setting).where(Setting.status == "confirmed").limit(30)
        ).all()
        prompt_row = session.get(ProjectSetting, "ai_system_prompt")
        history = session.scalars(
            select(AiMessage)
            .where(AiMessage.session_id == session_id)
            .order_by(AiMessage.created_at)
            .limit(20)
        ).all()

    system_prompt = (
        "你是网文创作设定助手。回答必须基于下面『已确认设定』，不得编造与设定矛盾的规则。"
        "如果用户提出的设定与已有设定冲突，明确指出来。回答使用中文。\n\n"
    )
    if prompt_row:
        system_prompt += f"作者额外要求：{prompt_row.value}\n\n"
    if confirmed:
        lines = "\n".join(f"- {s.title}：{s.content_md[:200]}" for s in confirmed)
        system_prompt += f"『已确认设定』\n{lines}"
    else:
        system_prompt += "『已确认设定』（暂无）"

    related = []
    try:
        from app.services import rag_service

        related = rag_service.search_vector(project_id, user_content[-300:], top_k=8)
    except Exception:
        related = []
    if related:
        lines = "\n".join(
            f"- [{item['type']}] {item['title']}：{item['snippet']}" for item in related
        )
        system_prompt += f"\n\n『相关检索』\n{lines}"

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend({"role": m.role, "content": m.content} for m in history)
    return system_prompt, messages


def chat(project_id: str, session_id: str, content: str) -> str:
    from fastapi import HTTPException

    if not settings.deepseek_api_key:
        raise HTTPException(status_code=503, detail="AI 凭证未配置（AI_NOVEL_DEEPSEEK_API_KEY）")

    with project_session(project_id) as session:
        if session.get(AiSession, session_id) is None:
            raise HTTPException(status_code=404, detail="会话不存在")
        session.add(AiMessage(id=new_id(), session_id=session_id, role="user", content=content))
        session.commit()

    _, messages = _build_context(project_id, session_id, content)
    try:
        resp = httpx.post(
            f"{settings.deepseek_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.deepseek_api_key}"},
            json={"model": settings.deepseek_model, "messages": messages, "temperature": 0.7},
            timeout=60,
        )
        resp.raise_for_status()
        reply = resp.json()["choices"][0]["message"]["content"].strip()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"AI 服务调用失败：{e}") from e

    with project_session(project_id) as session:
        session.add(AiMessage(id=new_id(), session_id=session_id, role="assistant", content=reply))
        ai_session = session.get(AiSession, session_id)
        if ai_session:
            from app.core.database import now_iso

            ai_session.updated_at = now_iso()
        session.commit()
    return reply


def get_prompt(project_id: str) -> dict:
    with project_session(project_id) as session:
        row = session.get(ProjectSetting, "ai_system_prompt")
        return {"prompt": row.value if row else ""}


def set_prompt(project_id: str, prompt: str) -> dict:
    with project_session(project_id) as session:
        row = session.get(ProjectSetting, "ai_system_prompt")
        if row is None:
            session.add(ProjectSetting(key="ai_system_prompt", value=prompt))
        else:
            row.value = prompt
        session.commit()
        return {"prompt": prompt}
