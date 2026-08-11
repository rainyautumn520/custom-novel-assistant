import re
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.core.database import AppSession, project_db_path, project_session
from app.models.chapter import Chapter
from app.models.app import Project
from app.models.outline import OutlineNode


def _safe_filename(name: str) -> str:
    cleaned = "".join(c for c in name if c not in '<>:"/\\|?*').strip()
    return cleaned or "未命名"


def _write_txt(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8-sig")
    tmp.replace(path)


def _exports_dir(project_id: str) -> Path:
    return project_db_path(project_id).parent / "exports"


def _resolve_output(project_id: str, output_path: str | None, default_name: str) -> Path:
    if output_path and output_path.strip():
        return Path(output_path.strip()).expanduser()
    return _exports_dir(project_id) / f"{_safe_filename(default_name)}.txt"


def _count_words(content: str) -> int:
    return len(re.findall(r"\S", content))


def export_single(
    project_id: str,
    chapter_id: str,
    include_title: bool = True,
    output_path: str | None = None,
) -> dict[str, Any]:
    from fastapi import HTTPException

    with project_session(project_id) as session:
        chapter = session.get(Chapter, chapter_id)
        if chapter is None:
            raise HTTPException(status_code=404, detail="章节不存在")
        title = chapter.title
        content = (project_db_path(project_id).parent / chapter.file_path).read_text(
            encoding="utf-8"
        )

    lines = []
    if include_title:
        lines.append(title)
        lines.append("")
    lines.append(content.rstrip("\n"))
    text = "\n".join(lines) + "\n"

    target = _resolve_output(project_id, output_path, title)
    _write_txt(target, text)
    return {
        "path": str(target),
        "wordCount": _count_words(content),
        "chaptersExported": 1,
        "chaptersSkipped": 0,
        "skippedTitles": [],
    }


def preview_book(project_id: str) -> dict[str, Any]:
    with project_session(project_id) as session:
        nodes = list(
            session.scalars(select(OutlineNode).order_by(OutlineNode.parent_id, OutlineNode.sort_order))
        )
        chapters = {c.id: c for c in session.scalars(select(Chapter))}

    volumes = sorted((n for n in nodes if n.level == "volume"), key=lambda n: n.sort_order)
    items = []
    total_words = 0
    skipped = 0
    for volume in volumes:
        chapter_nodes = sorted(
            (n for n in nodes if n.level == "chapter" and n.parent_id == volume.id),
            key=lambda n: n.sort_order,
        )
        for node in chapter_nodes:
            chapter = chapters.get(node.chapter_id) if node.chapter_id else None
            if chapter is None:
                skipped += 1
                items.append(
                    {
                        "volumeTitle": volume.title,
                        "chapterTitle": node.title,
                        "chapterId": None,
                        "wordCount": 0,
                        "status": "no_draft",
                    }
                )
                continue
            content = (project_db_path(project_id).parent / chapter.file_path).read_text(
                encoding="utf-8"
            )
            words = _count_words(content)
            total_words += words
            items.append(
                {
                    "volumeTitle": volume.title,
                    "chapterTitle": node.title,
                    "chapterId": chapter.id,
                    "wordCount": words,
                    "status": chapter.status,
                }
            )
    return {
        "totalWords": total_words,
        "exportedCount": len(items) - skipped,
        "skippedCount": skipped,
        "items": items,
    }


def export_book(
    project_id: str,
    include_volume: bool = True,
    include_chapter: bool = True,
    output_path: str | None = None,
) -> dict[str, Any]:
    from fastapi import HTTPException

    with project_session(project_id) as session:
        nodes = list(
            session.scalars(select(OutlineNode).order_by(OutlineNode.parent_id, OutlineNode.sort_order))
        )
        chapters = {c.id: c for c in session.scalars(select(Chapter))}

    with AppSession() as project_session_row:
        project = project_session_row.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="作品不存在")

    volumes = sorted((n for n in nodes if n.level == "volume"), key=lambda n: n.sort_order)
    parts: list[str] = []
    skipped_titles: list[str] = []
    exported = 0
    total_words = 0

    for volume in volumes:
        if include_volume:
            parts.append(volume.title)
            parts.append("")
        chapter_nodes = sorted(
            (n for n in nodes if n.level == "chapter" and n.parent_id == volume.id),
            key=lambda n: n.sort_order,
        )
        for node in chapter_nodes:
            chapter = chapters.get(node.chapter_id) if node.chapter_id else None
            if chapter is None:
                skipped_titles.append(node.title)
                continue
            content = (project_db_path(project_id).parent / chapter.file_path).read_text(
                encoding="utf-8"
            )
            if include_chapter:
                parts.append(chapter.title)
                parts.append("")
            parts.append(content.rstrip("\n"))
            parts.append("")
            parts.append("")
            exported += 1
            total_words += _count_words(content)

    text = "\n".join(parts).rstrip() + "\n"
    target = _resolve_output(project_id, output_path, f"{project.name}_全书")
    _write_txt(target, text)
    return {
        "path": str(target),
        "wordCount": total_words,
        "chaptersExported": exported,
        "chaptersSkipped": len(skipped_titles),
        "skippedTitles": skipped_titles,
    }
