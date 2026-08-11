from sqlalchemy import select

from app.core.database import new_id, project_db_path, project_session
from app.models.asset import Asset


def _safe_name(name: str) -> str:
    cleaned = "".join(c for c in name if c not in '<>:"/\\|?*').strip()
    return cleaned or "file"


def list_assets(project_id: str) -> list[Asset]:
    with project_session(project_id) as session:
        return list(session.scalars(select(Asset).order_by(Asset.updated_at.desc())))


def create_asset(project_id: str, data: dict) -> Asset:
    with project_session(project_id) as session:
        asset = Asset(**data)
        session.add(asset)
        session.commit()
        session.refresh(asset)
        return asset


def create_file_asset(
    project_id: str,
    filename: str,
    content: bytes,
    title: str,
    source: str = "",
    tags: list[str] | None = None,
) -> Asset:
    asset_id = new_id()
    safe_name = _safe_name(filename)
    asset_dir = project_db_path(project_id).parent / "assets" / asset_id
    asset_dir.mkdir(parents=True, exist_ok=True)
    file_path = asset_dir / safe_name
    file_path.write_bytes(content)
    relative = f"assets/{asset_id}/{safe_name}"
    with project_session(project_id) as session:
        asset = Asset(
            id=asset_id,
            title=title,
            kind="file",
            file_path=relative,
            source=source,
            tags=tags or [],
        )
        session.add(asset)
        session.commit()
        session.refresh(asset)
        return asset


def get_asset_or_404(project_id: str, asset_id: str) -> Asset:
    from fastapi import HTTPException

    with project_session(project_id) as session:
        asset = session.get(Asset, asset_id)
        if asset is None:
            raise HTTPException(status_code=404, detail="素材不存在")
        return asset


def get_file_path(project_id: str, asset: Asset):
    return project_db_path(project_id).parent / asset.file_path


def update_asset(project_id: str, asset_id: str, data: dict) -> Asset:
    from fastapi import HTTPException

    with project_session(project_id) as session:
        asset = session.get(Asset, asset_id)
        if asset is None:
            raise HTTPException(status_code=404, detail="素材不存在")
        for key, value in data.items():
            if value is not None:
                setattr(asset, key, value)
        session.commit()
        session.refresh(asset)
        return asset


def delete_asset(project_id: str, asset_id: str) -> None:
    from fastapi import HTTPException

    with project_session(project_id) as session:
        asset = session.get(Asset, asset_id)
        if asset is None:
            raise HTTPException(status_code=404, detail="素材不存在")
        if asset.kind == "file" and asset.file_path:
            file_path = project_db_path(project_id).parent / asset.file_path
            if file_path.exists():
                trash_dir = project_db_path(project_id).parent / ".trash"
                trash_dir.mkdir(parents=True, exist_ok=True)
                file_path.rename(trash_dir / file_path.name)
        session.delete(asset)
        session.commit()
