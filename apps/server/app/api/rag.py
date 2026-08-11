from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from sqlalchemy.orm import Session

from app.api.projects import get_app_session
from app.services import project_service, rag_service

router = APIRouter(prefix="/api/projects/{project_id}/rag", tags=["rag"])


class RagSearchRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    query: str = Field(min_length=1)
    top_k: int = 8


@router.post("/index")
def rebuild(project_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    return rag_service.rebuild_index(project_id)


@router.get("/status")
def get_status(project_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    return rag_service.status(project_id)


@router.post("/search")
def search(
    project_id: str, payload: RagSearchRequest, session: Session = Depends(get_app_session)
):
    project_service.get_project_or_404(session, project_id)
    return rag_service.search_vector(project_id, payload.query, payload.top_k)
