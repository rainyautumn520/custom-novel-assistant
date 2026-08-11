from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.projects import get_app_session
from app.schemas.asset import AssetCreate, AssetOut, AssetUpdate
from app.services import asset_service, project_service

router = APIRouter(prefix="/api/projects/{project_id}/assets", tags=["assets"])


@router.get("", response_model=list[AssetOut])
def list_assets(project_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    return asset_service.list_assets(project_id)


@router.post("", response_model=AssetOut, status_code=201)
def create_asset(
    project_id: str, payload: AssetCreate, session: Session = Depends(get_app_session)
):
    project_service.get_project_or_404(session, project_id)
    return asset_service.create_asset(project_id, payload.model_dump())


@router.get("/{asset_id}", response_model=AssetOut)
def get_asset(project_id: str, asset_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    return asset_service.get_asset_or_404(project_id, asset_id)


@router.put("/{asset_id}", response_model=AssetOut)
def update_asset(
    project_id: str,
    asset_id: str,
    payload: AssetUpdate,
    session: Session = Depends(get_app_session),
):
    project_service.get_project_or_404(session, project_id)
    return asset_service.update_asset(project_id, asset_id, payload.model_dump())


@router.delete("/{asset_id}", status_code=204)
def delete_asset(project_id: str, asset_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    asset_service.delete_asset(project_id, asset_id)
