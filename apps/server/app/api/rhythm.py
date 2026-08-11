from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.projects import get_app_session
from app.services import project_service, rhythm_service

router = APIRouter(prefix="/api/projects/{project_id}", tags=["rhythm"])


@router.get("/rhythm")
def rhythm(project_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    return rhythm_service.rhythm(project_id)
