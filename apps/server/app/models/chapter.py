from sqlalchemy import JSON, ForeignKey, String, Text
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


class ChapterCommit(NovelBase):
    """章节提交链记录（v0.4）：每次 commit 生成一条可审计的事实记录。"""

    __tablename__ = "chapter_commits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    chapter_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(16), default="accepted")
    accepted_events: Mapped[list] = mapped_column(JSON, default=list)
    state_deltas: Mapped[dict] = mapped_column(JSON, default=dict)
    entity_deltas: Mapped[list] = mapped_column(JSON, default=list)
    summary_text: Mapped[str] = mapped_column(Text, default="")
    projection_status: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[str] = mapped_column(String(32), default=now_iso)
