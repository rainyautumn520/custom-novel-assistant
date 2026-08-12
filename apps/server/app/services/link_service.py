from sqlalchemy import delete, select

from app.core.database import project_session
from app.models.link import EntityLink


def list_links_for(project_id: str, source_type: str, source_id: str) -> list[EntityLink]:
    with project_session(project_id) as session:
        return list(
            session.scalars(
                select(EntityLink).where(
                    EntityLink.source_type == source_type,
                    EntityLink.source_id == source_id,
                )
            )
        )


def replace_setting_links(
    project_id: str, character_id: str, setting_ids: list[str]
) -> list[EntityLink]:
    with project_session(project_id) as session:
        session.execute(
            delete(EntityLink).where(
                EntityLink.source_type == "character",
                EntityLink.source_id == character_id,
                EntityLink.target_type == "setting",
            )
        )
        links = [
            EntityLink(
                source_type="character",
                source_id=character_id,
                target_type="setting",
                target_id=setting_id,
                relation_type="refers_to",
            )
            for setting_id in setting_ids
        ]
        session.add_all(links)
        session.commit()
        for link in links:
            session.refresh(link)
        return links


def create_link(project_id: str, data: dict) -> EntityLink:
    """创建任意实体关系（图谱连线）。"""
    from fastapi import HTTPException

    with project_session(project_id) as session:
        exists = session.scalar(
            select(EntityLink).where(
                EntityLink.source_type == data["source_type"],
                EntityLink.source_id == data["source_id"],
                EntityLink.target_type == data["target_type"],
                EntityLink.target_id == data["target_id"],
                EntityLink.relation_type == data.get("relation_type", "refers_to"),
            )
        )
        if exists:
            return exists
        link = EntityLink(
            source_type=data["source_type"],
            source_id=data["source_id"],
            target_type=data["target_type"],
            target_id=data["target_id"],
            relation_type=data.get("relation_type", "refers_to"),
        )
        session.add(link)
        session.commit()
        session.refresh(link)
        return link


def delete_link(project_id: str, link_id: str) -> None:
    from fastapi import HTTPException

    with project_session(project_id) as session:
        link = session.get(EntityLink, link_id)
        if link is None:
            raise HTTPException(status_code=404, detail="关系不存在")
        session.delete(link)
        session.commit()
