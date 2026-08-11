import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select

from app.core.database import new_id, now_iso, project_db_path, project_session
from app.models.chapter import Chapter, ChapterSnapshot
from app.models.outline import OutlineNode

MAX_SNAPSHOTS = 20


def _count_words(content: str) -> int:
    return len(re.findall(r"\S", content))


def _sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _chapter_dir(project_id: str) -> Path:
    return project_db_path(project_id).parent / "chapters"


def list_chapters(project_id: str) -> list[Chapter]:
    with project_session(project_id) as session:
        return list(session.scalars(select(Chapter).order_by(Chapter.created_at)))


def create_chapter(project_id: str, title: str, outline_node_id: str | None = None) -> Chapter:
    with project_session(project_id) as session:
        if outline_node_id:
            node = session.get(OutlineNode, outline_node_id)
            if node is None:
                from fastapi import HTTPException

                raise HTTPException(status_code=404, detail="章纲不存在")
        chapter = Chapter(
            id=new_id(),
            title=title,
            outline_node_id=outline_node_id,
            file_path=f"chapters/{new_id()}.md",
        )
        session.add(chapter)
        session.commit()
        session.refresh(chapter)
        file_path = _chapter_dir(project_id) / chapter.file_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text("", encoding="utf-8")
        return chapter


def get_chapter(project_id: str, chapter_id: str) -> tuple[Chapter, str]:
    from fastapi import HTTPException

    with project_session(project_id) as session:
        chapter = session.get(Chapter, chapter_id)
        if chapter is None:
            raise HTTPException(status_code=404, detail="章节不存在")
        file_path = project_db_path(project_id).parent / chapter.file_path
        content = file_path.read_text(encoding="utf-8") if file_path.exists() else ""
        return chapter, content


def update_chapter(
    project_id: str,
    chapter_id: str,
    title: str | None = None,
    content_md: str | None = None,
) -> tuple[Chapter, str]:
    from fastapi import HTTPException

    with project_session(project_id) as session:
        chapter = session.get(Chapter, chapter_id)
        if chapter is None:
            raise HTTPException(status_code=404, detail="章节不存在")
        root = project_db_path(project_id).parent
        file_path = root / chapter.file_path

        current = file_path.read_text(encoding="utf-8") if file_path.exists() else ""
        if content_md is not None:
            if current.strip():
                _create_snapshot(project_id, root, chapter.id, current)
            tmp_dir = root / "chapters" / ".tmp"
            tmp_dir.mkdir(parents=True, exist_ok=True)
            tmp_path = tmp_dir / f"{chapter.id}.md.tmp"
            tmp_path.write_text(content_md, encoding="utf-8")
            file_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path.replace(file_path)
            chapter.word_count = _count_words(content_md)
            chapter.file_hash = _sha256(content_md)
        if title is not None:
            chapter.title = title.strip() or chapter.title
        session.commit()
        session.refresh(chapter)
        return chapter, content_md if content_md is not None else current


def _create_snapshot(project_id: str, root: Path, chapter_id: str, content: str) -> None:
    snap_dir = root / "snapshots" / chapter_id
    snap_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    name = f"{ts}_{_sha256(content)[:8]}.md"
    relative_path = f"snapshots/{chapter_id}/{name}"
    (snap_dir / name).write_text(content, encoding="utf-8")
    snapshots = sorted(snap_dir.glob("*.md"))
    for old in snapshots[:-MAX_SNAPSHOTS]:
        old.unlink(missing_ok=True)
    with project_session(project_id) as session:
        session.add(
            ChapterSnapshot(
                chapter_id=chapter_id,
                snapshot_path=relative_path,
                file_hash=_sha256(content),
                word_count=_count_words(content),
                note="auto",
            )
        )
        session.commit()


def delete_chapter(project_id: str, chapter_id: str) -> None:
    from fastapi import HTTPException

    with project_session(project_id) as session:
        chapter = session.get(Chapter, chapter_id)
        if chapter is None:
            raise HTTPException(status_code=404, detail="章节不存在")
        root = project_db_path(project_id).parent
        file_path = root / chapter.file_path
        if file_path.exists():
            trash_dir = root / ".trash"
            trash_dir.mkdir(parents=True, exist_ok=True)
            file_path.rename(trash_dir / file_path.name)
        if chapter.outline_node_id:
            node = session.get(OutlineNode, chapter.outline_node_id)
            if node and node.chapter_id == chapter.id:
                node.chapter_id = None
        session.delete(chapter)
        session.commit()
