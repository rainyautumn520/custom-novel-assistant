"""RAG 检索：文档切片 → 嵌入 → ChromaDB → 混合检索。"""

import time
import sys
from typing import Any

from sqlalchemy import select

from app.config import settings
from app.core.database import project_db_path, project_session
from app.core.vector_store import (
    backend_label,
    collection,
    embed,
    ollama_available,
    reset_collection,
)
from app.models.asset import Asset
from app.models.chapter import Chapter
from app.models.character import Character
from app.models.world import Setting

CHUNK_SIZE = 300
OVERLAP = 50


def _chunks(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= CHUNK_SIZE:
        return [text]
    step = CHUNK_SIZE - OVERLAP
    return [text[i : i + CHUNK_SIZE] for i in range(0, len(text), step)]


def _docs_for(project_id: str) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    with project_session(project_id) as session:
        for s in session.scalars(select(Setting).where(Setting.status == "confirmed")):
            for i, chunk in enumerate(_chunks(f"{s.title}：{s.content_md}")):
                docs.append(
                    {
                        "id": f"setting:{s.id}:{i}",
                        "doc": chunk,
                        "meta": {
                            "entity_type": "setting",
                            "entity_id": s.id,
                            "title": s.title,
                            "chunk": i,
                        },
                    }
                )
        for c in session.scalars(select(Character)):
            for i, chunk in enumerate(
                _chunks(f"{c.name}：{c.identity} {c.background} {c.goals}")
            ):
                docs.append(
                    {
                        "id": f"character:{c.id}:{i}",
                        "doc": chunk,
                        "meta": {
                            "entity_type": "character",
                            "entity_id": c.id,
                            "title": c.name,
                            "chunk": i,
                        },
                    }
                )
        for a in session.scalars(select(Asset)):
            for i, chunk in enumerate(_chunks(f"{a.title}：{a.content_md}")):
                docs.append(
                    {
                        "id": f"asset:{a.id}:{i}",
                        "doc": chunk,
                        "meta": {
                            "entity_type": "asset",
                            "entity_id": a.id,
                            "title": a.title,
                            "chunk": i,
                        },
                    }
                )
        for ch in session.scalars(select(Chapter)):
            file_path = project_db_path(project_id).parent / ch.file_path
            content = file_path.read_text(encoding="utf-8") if file_path.exists() else ""
            for i, chunk in enumerate(_chunks(f"{ch.title}：{content}")):
                docs.append(
                    {
                        "id": f"chapter:{ch.id}:{i}",
                        "doc": chunk,
                        "meta": {
                            "entity_type": "chapter",
                            "entity_id": ch.id,
                            "title": ch.title,
                            "chunk": i,
                        },
                    }
                )
    return docs


def rebuild_index(project_id: str) -> dict:
    col = reset_collection(project_id)
    docs = _docs_for(project_id)
    if not docs:
        return {"indexed": 0, "seconds": 0.0}
    t0 = time.perf_counter()
    ids = [d["id"] for d in docs]
    documents = [d["doc"] for d in docs]
    metadatas = [d["meta"] for d in docs]
    for start in range(0, len(docs), 256):
        batch = slice(start, start + 256)
        col.upsert(
            ids=ids[batch],
            documents=documents[batch],
            metadatas=metadatas[batch],
            embeddings=embed(documents[batch]),
        )
    return {"indexed": len(docs), "seconds": round(time.perf_counter() - t0, 2)}


def index_chapter(project_id: str, chapter_id: str) -> None:
    """章节保存后的增量更新（尽力而为，失败不阻断保存）。"""
    try:
        col = collection(project_id)
        if col.count() == 0:
            return
        col.delete(where={"entity_id": chapter_id, "entity_type": "chapter"})
        with project_session(project_id) as session:
            chapter = session.get(Chapter, chapter_id)
            if chapter is None:
                return
            file_path = project_db_path(project_id).parent / chapter.file_path
            content = file_path.read_text(encoding="utf-8") if file_path.exists() else ""
            chunks = _chunks(f"{chapter.title}：{content}")
        if not chunks:
            return
        ids = [f"chapter:{chapter_id}:{i}" for i in range(len(chunks))]
        col.upsert(
            ids=ids,
            documents=chunks,
            metadatas=[
                {
                    "entity_type": "chapter",
                    "entity_id": chapter_id,
                    "title": chapter.title,
                    "chunk": i,
                }
                for i in range(len(chunks))
            ],
            embeddings=embed(chunks),
        )
    except Exception as exc:  # 索引失败不影响正文保存
        print(f"[rag] index_chapter failed: {exc}", file=sys.stderr)


def search_vector(project_id: str, query: str, top_k: int = 8) -> list[dict]:
    col = collection(project_id)
    if col.count() == 0:
        return []
    query_embedding = embed([query])[0]
    result = col.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, col.count()),
        include=["documents", "metadatas", "distances"],
    )
    items = []
    for doc, meta, distance in zip(
        result["documents"][0], result["metadatas"][0], result["distances"][0]
    ):
        items.append(
            {
                "type": meta["entity_type"],
                "id": meta["entity_id"],
                "title": meta["title"],
                "snippet": doc[:120],
                "score": round(1.0 - distance, 4),
            }
        )
    return items


def status(project_id: str) -> dict:
    col = collection(project_id)
    return {
        "backend": backend_label(),
        "model": settings.vector_model,
        "count": col.count(),
        "ollamaAvailable": ollama_available(),
    }
