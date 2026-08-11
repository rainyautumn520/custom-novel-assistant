"""章节提交链：实体提取、事实入账、投影更新。"""

from sqlalchemy import select

from app.core.database import new_id, project_db_path, project_session
from app.models.asset import Asset
from app.models.chapter import Chapter, ChapterCommit
from app.models.character import Character
from app.models.link import EntityLink
from app.models.world import Setting


def _extract_entity_links(project_id: str, chapter_id: str, content: str) -> list[dict]:
    """扫描正文中出现的已有实体（设定/人物/素材），建立 chapter → entity 关系。"""
    created: list[dict] = []
    with project_session(project_id) as session:
        existing = {
            (l.source_id, l.target_type, l.target_id)
            for l in session.scalars(
                select(EntityLink).where(
                    EntityLink.source_type == "chapter",
                    EntityLink.source_id == chapter_id,
                )
            )
        }
        for setting in session.scalars(select(Setting)):
            if setting.title and setting.title in content:
                key = (chapter_id, "setting", setting.id)
                if key not in existing:
                    session.add(
                        EntityLink(
                            source_type="chapter",
                            source_id=chapter_id,
                            target_type="setting",
                            target_id=setting.id,
                            relation_type="appears_in",
                        )
                    )
                    created.append({"type": "setting", "id": setting.id, "title": setting.title})
        for character in session.scalars(select(Character)):
            names = [character.name, *character.aliases]
            for name in names:
                if name and name in content:
                    key = (chapter_id, "character", character.id)
                    if key not in existing:
                        session.add(
                            EntityLink(
                                source_type="chapter",
                                source_id=chapter_id,
                                target_type="character",
                                target_id=character.id,
                                relation_type="appears_in",
                            )
                        )
                        created.append({"type": "character", "id": character.id, "title": name})
                    break
        for asset in session.scalars(select(Asset)):
            if asset.title and asset.title in content:
                key = (chapter_id, "asset", asset.id)
                if key not in existing:
                    session.add(
                        EntityLink(
                            source_type="chapter",
                            source_id=chapter_id,
                            target_type="asset",
                            target_id=asset.id,
                            relation_type="appears_in",
                        )
                    )
                    created.append({"type": "asset", "id": asset.id, "title": asset.title})
        session.commit()
    return created


def commit_chapter(project_id: str, chapter_id: str) -> ChapterCommit:
    from fastapi import HTTPException

    with project_session(project_id) as session:
        chapter = session.get(Chapter, chapter_id)
        if chapter is None:
            raise HTTPException(status_code=404, detail="章节不存在")
        root = project_db_path(project_id).parent
        file_path = root / chapter.file_path
        content = file_path.read_text(encoding="utf-8") if file_path.exists() else ""
        if not content.strip():
            raise HTTPException(status_code=422, detail="空章节不能提交")

    entity_deltas = _extract_entity_links(project_id, chapter_id, content)
    summary = content.strip()[:200]

    projection = {"state": "done", "index": "done", "summary": "done"}
    try:
        from app.services import rag_service

        rag_service.index_chapter(project_id, chapter_id)
    except Exception:
        projection["index"] = "failed"

    with project_session(project_id) as session:
        commit = ChapterCommit(
            id=new_id(),
            chapter_id=chapter_id,
            status="accepted",
            accepted_events=[{"type": "chapter_committed", "chapter_id": chapter_id}],
            state_deltas={
                "chapter_status": "draft -> committed",
                "word_count": chapter.word_count,
            },
            entity_deltas=entity_deltas,
            summary_text=summary,
            projection_status=projection,
        )
        session.add(commit)
        chapter = session.get(Chapter, chapter_id)
        if chapter:
            chapter.status = "committed"
        session.commit()
        session.refresh(commit)
        return commit


def reject_commit(project_id: str, commit_id: str) -> ChapterCommit:
    from fastapi import HTTPException

    with project_session(project_id) as session:
        commit = session.get(ChapterCommit, commit_id)
        if commit is None:
            raise HTTPException(status_code=404, detail="提交记录不存在")
        commit.status = "rejected"
        chapter = session.get(Chapter, commit.chapter_id)
        if chapter and chapter.status == "committed":
            chapter.status = "draft"
        session.commit()
        session.refresh(commit)
        return commit


def list_commits(project_id: str) -> list[dict]:
    with project_session(project_id) as session:
        commits = list(
            session.scalars(select(ChapterCommit).order_by(ChapterCommit.created_at.desc()))
        )
        titles = {
            c.id: c.title for c in session.scalars(select(Chapter))
        }
        return [
            {
                **{k: getattr(c, k) for k in (
                    "id", "chapter_id", "status", "accepted_events",
                    "state_deltas", "entity_deltas", "summary_text",
                    "projection_status", "created_at",
                )},
                "chapter_title": titles.get(c.chapter_id, ""),
            }
            for c in commits
        ]


def list_chapter_commits(project_id: str, chapter_id: str) -> list[ChapterCommit]:
    with project_session(project_id) as session:
        return list(
            session.scalars(
                select(ChapterCommit)
                .where(ChapterCommit.chapter_id == chapter_id)
                .order_by(ChapterCommit.created_at.desc())
            )
        )
