from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.projects import get_app_session
from app.schemas.character import CharacterCreate, CharacterOut, CharacterUpdate
from app.services import character_service, project_service

router = APIRouter(prefix="/api/projects/{project_id}/characters", tags=["characters"])


@router.get("", response_model=list[CharacterOut])
def list_characters(project_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    return character_service.list_characters(project_id)


@router.post("", response_model=CharacterOut, status_code=201)
def create_character(
    project_id: str, payload: CharacterCreate, session: Session = Depends(get_app_session)
):
    project_service.get_project_or_404(session, project_id)
    return character_service.create_character(project_id, payload.model_dump())


@router.get("/{character_id}", response_model=CharacterOut)
def get_character(
    project_id: str, character_id: str, session: Session = Depends(get_app_session)
):
    project_service.get_project_or_404(session, project_id)
    return character_service.get_character_or_404(project_id, character_id)


@router.put("/{character_id}", response_model=CharacterOut)
def update_character(
    project_id: str,
    character_id: str,
    payload: CharacterUpdate,
    session: Session = Depends(get_app_session),
):
    project_service.get_project_or_404(session, project_id)
    return character_service.update_character(project_id, character_id, payload.model_dump())


@router.delete("/{character_id}", status_code=204)
def delete_character(
    project_id: str, character_id: str, session: Session = Depends(get_app_session)
):
    project_service.get_project_or_404(session, project_id)
    character_service.delete_character(project_id, character_id)
