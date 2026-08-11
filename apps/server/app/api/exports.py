from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from sqlalchemy.orm import Session

from app.api.projects import get_app_session
from app.services import export_service, project_service

router = APIRouter(prefix="/api/projects/{project_id}/exports", tags=["exports"])


class SingleExportRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    chapter_id: str
    include_title: bool = True
    output_path: str | None = None


class BookExportRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    include_volume: bool = True
    include_chapter: bool = True
    output_path: str | None = None


@router.get("/preview")
def preview(project_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    return export_service.preview_book(project_id)


@router.post("/single")
def export_single(
    project_id: str, payload: SingleExportRequest, session: Session = Depends(get_app_session)
):
    project_service.get_project_or_404(session, project_id)
    return export_service.export_single(
        project_id,
        chapter_id=payload.chapter_id,
        include_title=payload.include_title,
        output_path=payload.output_path,
    )


@router.post("/book")
def export_book(
    project_id: str, payload: BookExportRequest, session: Session = Depends(get_app_session)
):
    project_service.get_project_or_404(session, project_id)
    return export_service.export_book(
        project_id,
        include_volume=payload.include_volume,
        include_chapter=payload.include_chapter,
        output_path=payload.output_path,
    )
