from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.projects import get_app_session
from app.core.database import project_session
from app.models.link import EntityLink
from app.schemas.link import EntityLinkOut
from app.services import project_service

router = APIRouter(prefix="/api/projects/{project_id}", tags=["graph"])


@router.get("/links", response_model=list[EntityLinkOut])
def all_links(project_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    with project_session(project_id) as s:
        return list(s.scalars(select(EntityLink)))
