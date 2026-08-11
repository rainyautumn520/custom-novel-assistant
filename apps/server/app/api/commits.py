from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.projects import get_app_session
from app.schemas.commit import ChapterCommitListOut, ChapterCommitOut
from app.services import commit_service, project_service

router = APIRouter(prefix="/api/projects/{project_id}", tags=["commits"])


@router.post("/chapters/{chapter_id}/commit", response_model=ChapterCommitOut, status_code=201)
def commit_chapter(project_id: str, chapter_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    return commit_service.commit_chapter(project_id, chapter_id)


@router.get("/commits", response_model=list[ChapterCommitListOut])
def list_commits(project_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    return commit_service.list_commits(project_id)


@router.get("/chapters/{chapter_id}/commits", response_model=list[ChapterCommitOut])
def list_chapter_commits(
    project_id: str, chapter_id: str, session: Session = Depends(get_app_session)
):
    project_service.get_project_or_404(session, project_id)
    return commit_service.list_chapter_commits(project_id, chapter_id)


@router.post("/commits/{commit_id}/reject", response_model=ChapterCommitOut)
def reject_commit(project_id: str, commit_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    return commit_service.reject_commit(project_id, commit_id)
