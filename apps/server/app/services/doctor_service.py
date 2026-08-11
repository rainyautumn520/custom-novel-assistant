"""项目体检：悬空引用、未提交章节、空章节、无正文章纲、节奏断档、索引状态。"""

from sqlalchemy import select

from app.core.database import project_session
from app.models.asset import Asset
from app.models.chapter import Chapter
from app.models.character import Character
from app.models.link import EntityLink
from app.models.outline import OutlineNode
from app.models.world import Setting
from app.services.rhythm_service import STRAND_LIMITS, rhythm


def doctor(project_id: str) -> dict:
    checks = []
    with project_session(project_id) as session:
        chapters = list(session.scalars(select(Chapter)))
        chapter_ids = {c.id for c in chapters}
        links = list(session.scalars(select(EntityLink)))
        setting_ids = {s.id for s in session.scalars(select(Setting))}
        character_ids = {c.id for c in session.scalars(select(Character))}
        asset_ids = {a.id for a in session.scalars(select(Asset))}
        outline_ids = {n.id for n in session.scalars(select(OutlineNode))}
        chapter_nodes = [
            n for n in session.scalars(select(OutlineNode)) if n.level == "chapter"
        ]

    ids_by_type = {
        "setting": setting_ids,
        "character": character_ids,
        "chapter": chapter_ids,
        "asset": asset_ids,
        "outline": outline_ids,
    }
    dangling = [
        f"{l.source_type}:{l.source_id} -> {l.target_type}:{l.target_id}"
        for l in links
        if l.source_id not in ids_by_type.get(l.source_type, set())
        or l.target_id not in ids_by_type.get(l.target_type, set())
    ]
    checks.append(
        {
            "id": "dangling_links",
            "label": "悬空引用",
            "status": "fail" if dangling else "ok",
            "detail": f"{len(dangling)} 条关系指向缺失实体" + (f"（{dangling[0]}…）" if dangling else ""),
        }
    )

    uncommitted = [c for c in chapters if c.status != "committed"]
    checks.append(
        {
            "id": "uncommitted",
            "label": "未提交章节",
            "status": "warn" if uncommitted else "ok",
            "detail": f"{len(uncommitted)} / {len(chapters)} 章尚未提交",
        }
    )

    empty = [c for c in chapters if c.word_count == 0]
    checks.append(
        {
            "id": "empty_chapters",
            "label": "空章节",
            "status": "warn" if empty else "ok",
            "detail": f"{len(empty)} 章为空",
        }
    )

    no_draft = [n.title for n in chapter_nodes if not n.chapter_id]
    checks.append(
        {
            "id": "outline_without_draft",
            "label": "章纲无正文",
            "status": "warn" if no_draft else "ok",
            "detail": f"{len(no_draft)} 个章纲尚未创建正文" + (f"（{'、'.join(no_draft[:3])}…）" if no_draft else ""),
        }
    )

    rhythm_data = rhythm(project_id)
    for strand, limit in STRAND_LIMITS.items():
        stat = rhythm_data["strands"][strand]
        if stat["maxGap"] > limit:
            checks.append(
                {
                    "id": f"strand_gap_{strand}",
                    "label": f"{stat['label']}断档",
                    "status": "fail",
                    "detail": f"连续 {stat['maxGap']} 章未出现，超过红线 {limit} 章",
                }
            )

    if rhythm_data["openChekhovs"]:
        checks.append(
            {
                "id": "open_chekhovs",
                "label": "未回收伏笔",
                "status": "info",
                "detail": f"{rhythm_data['openChekhovs']} 条伏笔仍处于 open 状态",
            }
        )

    try:
        from app.services import rag_service

        vector_count = rag_service.status(project_id)["count"]
    except Exception:
        vector_count = 0
    checks.append(
        {
            "id": "vector_index",
            "label": "向量索引",
            "status": "warn" if vector_count == 0 else "ok",
            "detail": f"{vector_count} 个向量片段" if vector_count else "尚未建立，AI 检索不可用",
        }
    )

    healthy = all(c["status"] == "ok" for c in checks)
    return {
        "healthy": healthy,
        "summary": "项目健康" if healthy else "发现需要处理的问题",
        "checks": checks,
    }
