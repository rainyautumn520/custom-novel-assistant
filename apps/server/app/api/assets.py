from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
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


@router.post("/upload", response_model=AssetOut, status_code=201)
def upload_asset(
    project_id: str,
    file: UploadFile = File(...),
    title: str = Form(""),
    source: str = Form(""),
    tags: str = Form(""),
    session: Session = Depends(get_app_session),
):
    project_service.get_project_or_404(session, project_id)
    content = file.file.read()
    if not content:
        raise HTTPException(status_code=422, detail="文件为空")
    return asset_service.create_file_asset(
        project_id,
        filename=file.filename or "file",
        content=content,
        title=title or (file.filename or "未命名文件"),
        source=source,
        tags=[t.strip() for t in tags.split(",") if t.strip()],
    )


@router.get("/{asset_id}/file")
def download_asset(project_id: str, asset_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    asset = asset_service.get_asset_or_404(project_id, asset_id)
    if asset.kind != "file" or not asset.file_path:
        raise HTTPException(status_code=422, detail="该素材不是文件类型")
    file_path = asset_service.get_file_path(project_id, asset)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件已丢失")
    return FileResponse(
        file_path,
        filename=file_path.name,
        media_type="application/octet-stream",
    )


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
