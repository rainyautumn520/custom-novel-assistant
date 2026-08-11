from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.projects import get_app_session
from app.schemas.chapter import ChapterOut
from app.schemas.outline import OutlineCreate, OutlineOut, OutlineUpdate
from app.services import outline_service, project_service

router = APIRouter(prefix="/api/projects/{project_id}/outline", tags=["outline"])


@router.get("", response_model=list[OutlineOut])
def list_outline(project_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    return outline_service.list_outline(project_id)


@router.post("", response_model=OutlineOut, status_code=201)
def create_node(
    project_id: str, payload: OutlineCreate, session: Session = Depends(get_app_session)
):
    project_service.get_project_or_404(session, project_id)
    return outline_service.create_node(project_id, payload.model_dump())


@router.get("/{node_id}", response_model=OutlineOut)
def get_node(project_id: str, node_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    return outline_service.get_node_or_404(project_id, node_id)


@router.put("/{node_id}", response_model=OutlineOut)
def update_node(
    project_id: str,
    node_id: str,
    payload: OutlineUpdate,
    session: Session = Depends(get_app_session),
):
    project_service.get_project_or_404(session, project_id)
    return outline_service.update_node(project_id, node_id, payload.model_dump(exclude_unset=True))


@router.delete("/{node_id}", status_code=204)
def delete_node(project_id: str, node_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    outline_service.delete_node(project_id, node_id)


@router.post("/{node_id}/create-chapter", response_model=ChapterOut, status_code=201)
def create_chapter_from_node(
    project_id: str, node_id: str, session: Session = Depends(get_app_session)
):
    project_service.get_project_or_404(session, project_id)
    return outline_service.create_chapter_from_node(project_id, node_id)
