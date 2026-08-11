from sqlalchemy import select

from app.core.database import project_session
from app.models.world import Setting


def list_settings(project_id: str) -> list[Setting]:
    with project_session(project_id) as session:
        return list(session.scalars(select(Setting).order_by(Setting.updated_at.desc())))


def create_setting(project_id: str, data: dict) -> Setting:
    with project_session(project_id) as session:
        setting = Setting(**data)
        session.add(setting)
        session.commit()
        session.refresh(setting)
        return setting


def get_setting_or_404(project_id: str, setting_id: str) -> Setting:
    from fastapi import HTTPException

    with project_session(project_id) as session:
        setting = session.get(Setting, setting_id)
        if setting is None:
            raise HTTPException(status_code=404, detail="设定不存在")
        return setting


def update_setting(project_id: str, setting_id: str, data: dict) -> Setting:
    from fastapi import HTTPException

    with project_session(project_id) as session:
        setting = session.get(Setting, setting_id)
        if setting is None:
            raise HTTPException(status_code=404, detail="设定不存在")
        for key, value in data.items():
            if value is not None:
                setattr(setting, key, value)
        session.commit()
        session.refresh(setting)
        return setting


def delete_setting(project_id: str, setting_id: str) -> None:
    from fastapi import HTTPException

    with project_session(project_id) as session:
        setting = session.get(Setting, setting_id)
        if setting is None:
            raise HTTPException(status_code=404, detail="设定不存在")
        session.delete(setting)
        session.commit()
