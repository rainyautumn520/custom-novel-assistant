"""生成 RAG/性能验收测试数据：3 卷 30 章（每章约 1 万字）+ 设定/人物/素材。

用法（在 apps/server 下）：
    .venv\\Scripts\\python scripts\\seed_rag_data.py

默认把数据写到临时目录，不污染真实数据；可通过 AI_NOVEL_DATA_DIR 指定。
"""

import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault(
    "AI_NOVEL_DATA_DIR", tempfile.mkdtemp(prefix="ai-novel-ide-benchmark-")
)

from app.core.database import ensure_app_db  # noqa: E402
from app.services import (  # noqa: E402
    asset_service,
    chapter_service,
    rag_service,
    character_service,
    outline_service,
    project_service,
    search_service,
    setting_service,
)


def main() -> None:
    ensure_app_db()
    project = project_service.create_project(
        name="性能验收测试书",
        genre="玄幻",
        synopsis="用于 RAG 与性能验收的测试项目",
        target_words=300000,
    )
    pid = project.id

    t0 = time.perf_counter()
    for i in range(15):
        setting_service.create_setting(
            pid,
            {
                "title": f"设定{i + 1}：灵气复苏规则",
                "content_md": f"灵气复苏第{i + 1}条：天元历 1024 年起，灵脉浓度每十年翻倍，北境灵脉为源头。",
                "tags": ["规则", f"rule-{i + 1}"],
                "status": "confirmed",
            },
        )
    for i in range(10):
        character_service.create_character(
            pid,
            {
                "name": f"人物{i + 1}",
                "identity": "天元学宫弟子",
                "background": f"来自灵脉村，背景编号 {i + 1}。",
                "tags": ["测试"],
            },
        )
    for i in range(50):
        asset_service.create_asset(
            pid,
            {"title": f"素材{i + 1}", "content_md": f"北境地理与灵脉分布笔记 {i + 1}。", "tags": ["资料"]},
        )

    paragraph = "灵脉村外的晨雾尚未散尽，山道上已经传来脚步声。张小凡攥紧包袱，回头望了一眼村口的石坊。"
    for v in range(3):
        volume = outline_service.create_node(
            pid, {"level": "volume", "title": f"第{v + 1}卷", "sort_order": v}
        )
        for c in range(10):
            node = outline_service.create_node(
                pid,
                {
                    "level": "chapter",
                    "parent_id": volume.id,
                    "title": f"第{v * 10 + c + 1}章",
                    "sort_order": c,
                    "target_words": 10000,
                    "status": "done",
                },
            )
            chapter = outline_service.create_chapter_from_node(pid, node.id)
            content = (paragraph * 60)[:10000]
            chapter_service.update_chapter(pid, chapter.id, content_md=content)

    t_seed = time.perf_counter() - t0

    t1 = time.perf_counter()
    hits = search_service.search(pid, "灵脉")
    t_search = time.perf_counter() - t1

    t2 = time.perf_counter()
    chapters = chapter_service.list_chapters(pid)
    t_list = time.perf_counter() - t2

    t3 = time.perf_counter()
    index = rag_service.rebuild_index(pid)
    t_index = time.perf_counter() - t3

    t4 = time.perf_counter()
    vector_hits = rag_service.search_vector(pid, "灵脉枯竭的真相", top_k=5)
    t_vector = time.perf_counter() - t4

    print(
        {
            "projectId": pid,
            "seedSeconds": round(t_seed, 2),
            "chapters": len(chapters),
            "searchHits": len(hits),
            "searchSeconds": round(t_search, 4),
            "listChaptersSeconds": round(t_list, 4),
            "totalWords": sum(chapter.word_count for chapter in chapters),
            "vectorIndexSeconds": round(t_index, 2),
            "vectorIndexed": index["indexed"],
            "vectorSearchSeconds": round(t_vector, 4),
            "vectorTopHit": vector_hits[0] if vector_hits else None,
        }
    )


if __name__ == "__main__":
    main()
