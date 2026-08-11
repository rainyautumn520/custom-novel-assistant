from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import NovelBase, new_id, now_iso


class Chapter(NovelBase):
    __tablename__ = "chapters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    outline_node_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("outline_nodes.id", ondelete="SET NULL"), nullable=True
    )
    word_count: Mapped[int] = mapped_column(default=0)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), default="")
    status: Mapped[str] = mapped_column(String(16), default="draft")
    created_at: Mapped[str] = mapped_column(String(32), default=now_iso)
    updated_at: Mapped[str] = mapped_column(String(32), default=now_iso, onupdate=now_iso)


class ChapterSnapshot(NovelBase):
    __tablename__ = "chapter_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    chapter_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False
    )
    snapshot_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    word_count: Mapped[int] = mapped_column(default=0)
    note: Mapped[str] = mapped_column(String(200), default="auto")
    created_at: Mapped[str] = mapped_column(String(32), default=now_iso)
