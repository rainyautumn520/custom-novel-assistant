from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    assets,
    ai,
    categories,
    chapters,
    characters,
    commits,
    covers,
    exports,
    graph,
    links,
    outlines,
    projects,
    rag,
    search,
    settings,
    writing,
)
from app.config import settings as app_settings
from app.core.database import ensure_app_db

APP_VERSION = "0.4.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_app_db()
    yield


app = FastAPI(
    title="AI Novel IDE API",
    version=APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(settings.router)
app.include_router(characters.router)
app.include_router(categories.router)
app.include_router(outlines.router)
app.include_router(chapters.router)
app.include_router(exports.router)
app.include_router(links.router)
app.include_router(assets.router)
app.include_router(ai.router)
app.include_router(covers.router)
app.include_router(graph.router)
app.include_router(search.router)
app.include_router(rag.router)
app.include_router(writing.router)
app.include_router(commits.router)


@app.get("/api/health", tags=["meta"])
def health():
    return {
        "status": "ok",
        "version": APP_VERSION,
        "data_dir": str(app_settings.data_dir),
    }
