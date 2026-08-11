from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.projects import get_app_session
from app.schemas.setting import SettingCreate, SettingOut, SettingUpdate
from app.services import project_service, setting_service

router = APIRouter(prefix="/api/projects/{project_id}/settings", tags=["settings"])


@router.get("", response_model=list[SettingOut])
def list_settings(project_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    return setting_service.list_settings(project_id)


@router.post("", response_model=SettingOut, status_code=201)
def create_setting(
    project_id: str, payload: SettingCreate, session: Session = Depends(get_app_session)
):
    project_service.get_project_or_404(session, project_id)
    return setting_service.create_setting(project_id, payload.model_dump())


@router.get("/{setting_id}", response_model=SettingOut)
def get_setting(project_id: str, setting_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    return setting_service.get_setting_or_404(project_id, setting_id)


@router.put("/{setting_id}", response_model=SettingOut)
def update_setting(
    project_id: str,
    setting_id: str,
    payload: SettingUpdate,
    session: Session = Depends(get_app_session),
):
    project_service.get_project_or_404(session, project_id)
    return setting_service.update_setting(project_id, setting_id, payload.model_dump())


@router.delete("/{setting_id}", status_code=204)
def delete_setting(project_id: str, setting_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    setting_service.delete_setting(project_id, setting_id)
