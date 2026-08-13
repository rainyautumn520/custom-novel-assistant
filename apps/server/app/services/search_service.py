from sqlalchemy import String, or_, select

from app.core.database import project_db_path, project_session
from app.models.asset import Asset
from app.models.chapter import Chapter
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
        for chapter in session.scalars(
            select(Chapter).where(Chapter.title.ilike(f"%{q}%"))
        ):
            results.append(
                {
                    "type": "chapter",
                    "id": chapter.id,
                    "title": chapter.title,
                    "snippet": f"章节 · {chapter.word_count} 字",
                }
            )
        # 正文内容搜索（读文件，命中则给出所在章节）
        for chapter in session.scalars(select(Chapter)):
            path = project_db_path(project_id).parent / chapter.file_path
            if not path.exists():
                continue
            content = path.read_text(encoding="utf-8")
            if q in content.lower():
                index = content.lower().find(q)
                snippet = content[max(0, index - 30) : index + 60].replace("\n", " ")
                results.append(
                    {
                        "type": "chapter",
                        "id": chapter.id,
                        "title": chapter.title,
                        "snippet": f"…{snippet}…",
                    }
                )
    return results
