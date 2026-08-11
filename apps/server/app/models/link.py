from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import NovelBase, new_id, now_iso


class EntityLink(NovelBase):
    __tablename__ = "entity_links"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_id: Mapped[str] = mapped_column(String(36), nullable=False)
    target_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_id: Mapped[str] = mapped_column(String(36), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(50), default="refers_to")
    created_at: Mapped[str] = mapped_column(String(32), default=now_iso)
