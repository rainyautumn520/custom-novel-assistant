from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from sqlalchemy.orm import Session

from app.api.projects import get_app_session
from app.services import project_service, writing_service

router = APIRouter(prefix="/api/projects/{project_id}", tags=["writing"])


class AssistRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    mode: str = Field(pattern="^(continue|rewrite)$")
    selection: str = ""
    instructions: str = ""


@router.post("/brief/{node_id}")
def brief(project_id: str, node_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    return writing_service.build_brief(project_id, node_id)


@router.post("/chapters/{chapter_id}/assist")
def assist(
    project_id: str,
    chapter_id: str,
    payload: AssistRequest,
    session: Session = Depends(get_app_session),
):
    project_service.get_project_or_404(session, project_id)
    return writing_service.assist(
        project_id,
        chapter_id,
        mode=payload.mode,
        selection=payload.selection,
        instructions=payload.instructions,
    )


@router.post("/chapters/{chapter_id}/review")
def review(project_id: str, chapter_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    return writing_service.review(project_id, chapter_id)
