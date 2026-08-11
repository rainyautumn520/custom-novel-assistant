from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import AppSession
from app.schemas.project import ProjectCreate, ProjectOut
from app.services import project_service

router = APIRouter(prefix="/api/projects", tags=["projects"])


def get_app_session():
    with AppSession() as session:
        yield session


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(payload: ProjectCreate, session: Session = Depends(get_app_session)):
    project = project_service.create_project(
        name=payload.name,
        genre=payload.genre,
        synopsis=payload.synopsis,
        target_words=payload.target_words,
    )
    return project


@router.get("", response_model=list[ProjectOut])
def list_projects(session: Session = Depends(get_app_session)):
    return project_service.list_projects()


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: str, session: Session = Depends(get_app_session)):
    return project_service.get_project_or_404(session, project_id)
