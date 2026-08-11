from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.projects import get_app_session
from app.schemas.chapter import ChapterCreate, ChapterDetail, ChapterOut, ChapterUpdate
from app.services import chapter_service, project_service

router = APIRouter(prefix="/api/projects/{project_id}/chapters", tags=["chapters"])


@router.get("", response_model=list[ChapterOut])
def list_chapters(project_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    return chapter_service.list_chapters(project_id)


@router.post("", response_model=ChapterOut, status_code=201)
def create_chapter(
    project_id: str, payload: ChapterCreate, session: Session = Depends(get_app_session)
):
    project_service.get_project_or_404(session, project_id)
    return chapter_service.create_chapter(
        project_id, payload.title, payload.outline_node_id
    )


@router.get("/{chapter_id}", response_model=ChapterDetail)
def get_chapter(project_id: str, chapter_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    chapter, content = chapter_service.get_chapter(project_id, chapter_id)
    return {**chapter.__dict__, "content_md": content}


@router.put("/{chapter_id}", response_model=ChapterDetail)
def update_chapter(
    project_id: str,
    chapter_id: str,
    payload: ChapterUpdate,
    session: Session = Depends(get_app_session),
):
    project_service.get_project_or_404(session, project_id)
    chapter, content = chapter_service.update_chapter(
        project_id, chapter_id, title=payload.title, content_md=payload.content_md
    )
    return {**chapter.__dict__, "content_md": content}


@router.delete("/{chapter_id}", status_code=204)
def delete_chapter(project_id: str, chapter_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    chapter_service.delete_chapter(project_id, chapter_id)
