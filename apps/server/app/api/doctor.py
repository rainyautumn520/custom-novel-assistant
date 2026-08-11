from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.projects import get_app_session
from app.services import doctor_service, project_service

router = APIRouter(prefix="/api/projects/{project_id}", tags=["doctor"])


@router.get("/doctor")
def doctor(project_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    return doctor_service.doctor(project_id)
