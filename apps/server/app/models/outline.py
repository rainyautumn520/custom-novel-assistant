from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import NovelBase, new_id, now_iso


class OutlineNode(NovelBase):
    __tablename__ = "outline_nodes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    parent_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("outline_nodes.id", ondelete="RESTRICT"), nullable=True
    )
    level: Mapped[str] = mapped_column(String(16), nullable=False)
    sort_order: Mapped[int] = mapped_column(default=0)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    goal: Mapped[str] = mapped_column(Text, default="")
    must_cover: Mapped[list] = mapped_column(JSON, default=list)
    forbidden: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(16), default="draft")
    target_words: Mapped[int] = mapped_column(default=0)
    strands: Mapped[list] = mapped_column(JSON, default=list)
    chapter_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("chapters.id", ondelete="SET NULL", use_alter=True),
        nullable=True,
    )
    created_at: Mapped[str] = mapped_column(String(32), default=now_iso)
    updated_at: Mapped[str] = mapped_column(String(32), default=now_iso, onupdate=now_iso)
