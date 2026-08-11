from sqlalchemy import String, or_, select

from app.core.database import project_session
from app.models.asset import Asset
from app.models.character import Character
from app.models.world import Setting


def search(project_id: str, query: str) -> list[dict]:
    q = query.strip().lower()
    if not q:
        return []
    results: list[dict] = []
    with project_session(project_id) as session:
        for setting in session.scalars(
            select(Setting).where(
                or_(
                    Setting.title.ilike(f"%{q}%"),
                    Setting.content_md.ilike(f"%{q}%"),
                    Setting.tags.cast(String).ilike(f"%{q}%"),
                )
            )
        ):
            results.append(
                {
                    "type": "setting",
                    "id": setting.id,
                    "title": setting.title,
                    "snippet": setting.content_md[:120],
                }
            )
        for character in session.scalars(
            select(Character).where(
                or_(
                    Character.name.ilike(f"%{q}%"),
                    Character.identity.ilike(f"%{q}%"),
                    Character.background.ilike(f"%{q}%"),
                )
            )
        ):
            results.append(
                {
                    "type": "character",
                    "id": character.id,
                    "title": character.name,
                    "snippet": character.identity[:120],
                }
            )
        for asset in session.scalars(
            select(Asset).where(
                or_(
                    Asset.title.ilike(f"%{q}%"),
                    Asset.content_md.ilike(f"%{q}%"),
                    Asset.tags.cast(String).ilike(f"%{q}%"),
                )
            )
        ):
            results.append(
                {
                    "type": "asset",
                    "id": asset.id,
                    "title": asset.title,
                    "snippet": asset.content_md[:120],
                }
            )
    return results
