from sqlalchemy import func, select

from app.core.database import project_session
from app.models.world import SettingCategory


def list_categories(project_id: str) -> list[SettingCategory]:
    with project_session(project_id) as session:
        return list(
            session.scalars(select(SettingCategory).order_by(SettingCategory.sort_order))
        )


def create_category(project_id: str, data: dict) -> SettingCategory:
    with project_session(project_id) as session:
        category = SettingCategory(**data)
        session.add(category)
        session.commit()
        session.refresh(category)
        return category


def get_category_or_404(project_id: str, category_id: str) -> SettingCategory:
    from fastapi import HTTPException

    with project_session(project_id) as session:
        category = session.get(SettingCategory, category_id)
        if category is None:
            raise HTTPException(status_code=404, detail="分类不存在")
        return category


def update_category(project_id: str, category_id: str, data: dict) -> SettingCategory:
    from fastapi import HTTPException

    with project_session(project_id) as session:
        category = session.get(SettingCategory, category_id)
        if category is None:
            raise HTTPException(status_code=404, detail="分类不存在")
        for key, value in data.items():
            if value is not None:
                setattr(category, key, value)
        session.commit()
        session.refresh(category)
        return category


def delete_category(project_id: str, category_id: str) -> None:
    from fastapi import HTTPException

    with project_session(project_id) as session:
        category = session.get(SettingCategory, category_id)
        if category is None:
            raise HTTPException(status_code=404, detail="分类不存在")
        count = session.scalar(
            select(func.count())
            .select_from(SettingCategory)
            .where(SettingCategory.parent_id == category_id)
        )
        if count:
            raise HTTPException(status_code=409, detail="分类下还有子分类")
        session.delete(category)
        session.commit()
