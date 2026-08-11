from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from sqlalchemy.orm import Session

from app.api.projects import get_app_session
from app.core.database import project_db_path
from app.schemas.cover import CoverTaskOut
from app.services import cover_service, project_service

router = APIRouter(prefix="/api/projects/{project_id}/covers", tags=["covers"])


class CoverCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    prompt: str = Field(min_length=1)
    params: dict = {}


class ComposeRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    title: str = ""
    author: str = ""


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


@router.get("/{task_id}/file")
def task_file(project_id: str, task_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    task = cover_service.get_task_or_404(project_id, task_id)
    if not task.result_path:
        raise HTTPException(status_code=404, detail="该任务没有生成结果")
    file_path = project_db_path(project_id).parent / task.result_path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="图片文件已丢失")
    return FileResponse(file_path, media_type="image/png")


@router.post("/{task_id}/compose", response_model=CoverTaskOut)
def compose(
    project_id: str,
    task_id: str,
    payload: ComposeRequest,
    session: Session = Depends(get_app_session),
):
    project_service.get_project_or_404(session, project_id)
    return cover_service.compose_cover(project_id, task_id, payload.title, payload.author)


@router.get("/{task_id}/composed")
def composed_file(project_id: str, task_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    task = cover_service.get_task_or_404(project_id, task_id)
    if not task.composed_path:
        raise HTTPException(status_code=404, detail="该任务还没有合成图")
    file_path = project_db_path(project_id).parent / task.composed_path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="合成图文件已丢失")
    return FileResponse(file_path, media_type="image/png")
