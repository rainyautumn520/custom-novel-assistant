from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.projects import get_app_session
from app.schemas.chekhov import ChekhovCreate, ChekhovOut, ChekhovUpdate
from app.services import chekhov_service, project_service

router = APIRouter(prefix="/api/projects/{project_id}/chekhovs", tags=["chekhovs"])


@router.get("", response_model=list[ChekhovOut])
def list_chekhovs(project_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    return chekhov_service.list_chekhovs(project_id)


@router.post("", response_model=ChekhovOut, status_code=201)
def create_chekhov(
    project_id: str, payload: ChekhovCreate, session: Session = Depends(get_app_session)
):
    project_service.get_project_or_404(session, project_id)
    return chekhov_service.create_chekhov(project_id, payload.model_dump())


@router.put("/{chekhov_id}", response_model=ChekhovOut)
def update_chekhov(
    project_id: str,
    chekhov_id: str,
    payload: ChekhovUpdate,
    session: Session = Depends(get_app_session),
):
    project_service.get_project_or_404(session, project_id)
    return chekhov_service.update_chekhov(project_id, chekhov_id, payload.model_dump())


@router.delete("/{chekhov_id}", status_code=204)
def delete_chekhov(
    project_id: str, chekhov_id: str, session: Session = Depends(get_app_session)
):
    project_service.get_project_or_404(session, project_id)
    chekhov_service.delete_chekhov(project_id, chekhov_id)
