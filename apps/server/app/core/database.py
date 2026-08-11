from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


def now_iso() -> str:
    """ISO8601 UTC 时间戳（数据模型约定：所有时间戳为 TEXT）。"""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id() -> str:
    return str(uuid4())


class AppBase(DeclarativeBase):
    """app.db 元数据。"""


class NovelBase(DeclarativeBase):
    """novel.db（每作品库）元数据。"""


def _engine(db_path: Path):
    return create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )


app_engine = _engine(settings.data_dir / "app.db")
AppSession = sessionmaker(bind=app_engine, autoflush=False, expire_on_commit=False)


def project_db_path(project_id: str) -> Path:
    return settings.data_dir / "workspaces" / project_id / "novel.db"


def project_engine(project_id: str):
    return _engine(project_db_path(project_id))


def project_session(project_id: str):
    return sessionmaker(
        bind=project_engine(project_id),
        autoflush=False,
        expire_on_commit=False,
    )()


def ensure_app_db() -> None:
    """确保应用级数据库与表存在。"""
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    AppBase.metadata.create_all(app_engine)


def ensure_project_db(project_id: str) -> None:
    """确保作品库与表存在（骨架阶段用 create_all，迁移链接入后走 Alembic）。"""
    project_db_path(project_id).parent.mkdir(parents=True, exist_ok=True)
    NovelBase.metadata.create_all(project_engine(project_id))
