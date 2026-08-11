from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from sqlalchemy.orm import Session

from app.api.projects import get_app_session
from app.schemas.cover import CoverTaskOut
from app.services import cover_service, project_service

router = APIRouter(prefix="/api/projects/{project_id}/covers", tags=["covers"])


class CoverCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    prompt: str = Field(min_length=1)
    params: dict = {}


@router.get("", response_model=list[CoverTaskOut])
def list_tasks(project_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    return cover_service.list_tasks(project_id)


@router.post("", response_model=CoverTaskOut, status_code=201)
def create_task(
    project_id: str, payload: CoverCreate, session: Session = Depends(get_app_session)
):
    project_service.get_project_or_404(session, project_id)
    return cover_service.create_task(project_id, payload.prompt, payload.params)
