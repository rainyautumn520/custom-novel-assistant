"""向量库接入层：ChromaDB + 可切换嵌入后端（sentence-transformers / Ollama）。"""

import threading

import httpx
from chromadb import PersistentClient

from app.config import settings
from app.core.database import project_db_path

_st_model = None
_st_lock = threading.Lock()


def _st_embed(texts: list[str]) -> list[list[float]]:
    global _st_model
    with _st_lock:
        if _st_model is None:
            from sentence_transformers import SentenceTransformer

            _st_model = SentenceTransformer(settings.vector_model)
        return _st_model.encode(texts, normalize_embeddings=True).tolist()


def _ollama_embed(texts: list[str]) -> list[list[float]]:
    resp = httpx.post(
        f"{settings.ollama_base_url.rstrip('/')}/api/embed",
        json={"model": settings.vector_model, "input": texts},
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json()["embeddings"]


def embed(texts: list[str]) -> list[list[float]]:
    if settings.vector_backend == "ollama":
        return _ollama_embed(texts)
    return _st_embed(texts)


def backend_label() -> str:
    return f"{settings.vector_backend}:{settings.vector_model}"


def ollama_available() -> bool:
    try:
        resp = httpx.get(f"{settings.ollama_base_url.rstrip('/')}/api/tags", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


def collection(project_id: str):
    vectors_dir = project_db_path(project_id).parent / "vectors"
    client = PersistentClient(path=str(vectors_dir))
    return client.get_or_create_collection(
        "novel", metadata={"hnsw:space": "cosine"}
    )


def reset_collection(project_id: str):
    vectors_dir = project_db_path(project_id).parent / "vectors"
    client = PersistentClient(path=str(vectors_dir))
    try:
        client.delete_collection("novel")
    except Exception:
        pass
    return client.get_or_create_collection(
        "novel", metadata={"hnsw:space": "cosine"}
    )
