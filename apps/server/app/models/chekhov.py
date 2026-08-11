from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import NovelBase, new_id, now_iso


class Chekhov(NovelBase):
    """伏笔：埋设章 → 回收章，状态可追踪。"""

    __tablename__ = "chekhovs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    planted_chapter_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("chapters.id", ondelete="SET NULL"), nullable=True
    )
    payoff_chapter_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("chapters.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(16), default="open")  # open | resolved | abandoned
    created_at: Mapped[str] = mapped_column(String(32), default=now_iso)
    updated_at: Mapped[str] = mapped_column(String(32), default=now_iso, onupdate=now_iso)
