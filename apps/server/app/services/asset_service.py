from sqlalchemy import select

from app.core.database import project_session
from app.models.asset import Asset


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


def get_asset_or_404(project_id: str, asset_id: str) -> Asset:
    from fastapi import HTTPException

    with project_session(project_id) as session:
        asset = session.get(Asset, asset_id)
        if asset is None:
            raise HTTPException(status_code=404, detail="素材不存在")
        return asset


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
        session.delete(asset)
        session.commit()
