from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.projects import get_app_session
from app.schemas.ai import (
    AiChatReply,
    AiChatRequest,
    AiMessageOut,
    AiPromptUpdate,
    AiSessionCreate,
    AiSessionOut,
)
from app.services import ai_service, project_service
from app.services.ai_service import list_messages

router = APIRouter(prefix="/api/projects/{project_id}/ai", tags=["ai"])


@router.get("/sessions", response_model=list[AiSessionOut])
def sessions(project_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    return ai_service.list_sessions(project_id)


@router.post("/sessions", response_model=AiSessionOut, status_code=201)
def create_session(
    project_id: str, payload: AiSessionCreate, session: Session = Depends(get_app_session)
):
    project_service.get_project_or_404(session, project_id)
    return ai_service.create_session(project_id, payload.title)


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(
    project_id: str, session_id: str, session: Session = Depends(get_app_session)
):
    project_service.get_project_or_404(session, project_id)
    ai_service.delete_session(project_id, session_id)


@router.get("/sessions/{session_id}/messages", response_model=list[AiMessageOut])
def messages(project_id: str, session_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    return list_messages(project_id, session_id)


@router.post("/sessions/{session_id}/chat", response_model=AiChatReply)
def chat(
    project_id: str,
    session_id: str,
    payload: AiChatRequest,
    session: Session = Depends(get_app_session),
):
    project_service.get_project_or_404(session, project_id)
    return AiChatReply(reply=ai_service.chat(project_id, session_id, payload.content))


@router.get("/prompt", response_model=AiPromptUpdate)
def get_prompt(project_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    return ai_service.get_prompt(project_id)


@router.put("/prompt", response_model=AiPromptUpdate)
def set_prompt(
    project_id: str, payload: AiPromptUpdate, session: Session = Depends(get_app_session)
):
    project_service.get_project_or_404(session, project_id)
    return ai_service.set_prompt(project_id, payload.prompt)
