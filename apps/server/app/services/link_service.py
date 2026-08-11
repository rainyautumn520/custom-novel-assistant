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
