"""Strand Weave 节奏统计：Quest 主线 / Fire 感情线 / Constellation 世界观。"""

from sqlalchemy import func, select

from app.core.database import project_session
from app.models.chapter import Chapter
from app.models.chekhov import Chekhov
from app.models.outline import OutlineNode

STRAND_LIMITS = {"quest": 5, "fire": 10, "constellation": 15}
STRAND_LABELS = {"quest": "主线", "fire": "感情线", "constellation": "世界观"}


def rhythm(project_id: str) -> dict:
    with project_session(project_id) as session:
        nodes = list(
            session.scalars(select(OutlineNode).order_by(OutlineNode.parent_id, OutlineNode.sort_order))
        )
        chapters = {c.id: c for c in session.scalars(select(Chapter))}
        open_chekhovs = session.scalar(
            select(func.count()).select_from(Chekhov).where(Chekhov.status == "open")
        )

    volumes = sorted((n for n in nodes if n.level == "volume"), key=lambda n: n.sort_order)
    timeline = []
    sequences: dict[str, list[int]] = {s: [] for s in STRAND_LIMITS}
    for volume in volumes:
        chapter_nodes = sorted(
            (n for n in nodes if n.level == "chapter" and n.parent_id == volume.id),
            key=lambda n: n.sort_order,
        )
        for node in chapter_nodes:
            chapter = chapters.get(node.chapter_id) if node.chapter_id else None
            timeline.append(
                {
                    "chapterId": node.id,
                    "chapterTitle": node.title,
                    "volumeTitle": volume.title,
                    "status": chapter.status if chapter else "no_draft",
                    "words": chapter.word_count if chapter else 0,
                    "strands": node.strands or [],
                }
            )
            for strand in STRAND_LIMITS:
                sequences[strand].append(1 if strand in (node.strands or []) else 0)

    stats = {}
    for strand, limit in STRAND_LIMITS.items():
        seq = sequences[strand]
        total = len(seq)
        covered = sum(seq)
        max_gap = 0
        current = 0
        for value in seq:
            if value:
                current = 0
            else:
                current += 1
                max_gap = max(max_gap, current)
        stats[strand] = {
            "label": STRAND_LABELS[strand],
            "chapters": covered,
            "ratio": round(covered / total, 2) if total else 0,
            "maxGap": max_gap,
            "limit": limit,
            "ok": max_gap <= limit,
        }
    return {"strands": stats, "timeline": timeline, "openChekhovs": open_chekhovs or 0}
