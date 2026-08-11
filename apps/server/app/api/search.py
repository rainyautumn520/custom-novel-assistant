from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from sqlalchemy.orm import Session

from app.api.projects import get_app_session
from app.services import project_service, search_service

router = APIRouter(prefix="/api/projects/{project_id}/search", tags=["search"])


class SearchRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    query: str = Field(min_length=1)


@router.post("")
def search(
    project_id: str, payload: SearchRequest, session: Session = Depends(get_app_session)
):
    project_service.get_project_or_404(session, project_id)
    return search_service.search(project_id, payload.query)
