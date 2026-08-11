from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import categories, chapters, characters, outlines, projects, settings
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


@app.get("/api/health", tags=["meta"])
def health():
    return {
        "status": "ok",
        "version": APP_VERSION,
        "data_dir": str(app_settings.data_dir),
    }
