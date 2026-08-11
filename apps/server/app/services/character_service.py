from sqlalchemy import select

from app.core.database import project_session
from app.models.character import Character


def list_characters(project_id: str) -> list[Character]:
    with project_session(project_id) as session:
        return list(session.scalars(select(Character).order_by(Character.updated_at.desc())))


def create_character(project_id: str, data: dict) -> Character:
    with project_session(project_id) as session:
        character = Character(**data)
        session.add(character)
        session.commit()
        session.refresh(character)
        return character


def get_character_or_404(project_id: str, character_id: str) -> Character:
    from fastapi import HTTPException

    with project_session(project_id) as session:
        character = session.get(Character, character_id)
        if character is None:
            raise HTTPException(status_code=404, detail="人物不存在")
        return character


def update_character(project_id: str, character_id: str, data: dict) -> Character:
    from fastapi import HTTPException

    with project_session(project_id) as session:
        character = session.get(Character, character_id)
        if character is None:
            raise HTTPException(status_code=404, detail="人物不存在")
        for key, value in data.items():
            if value is not None:
                setattr(character, key, value)
        session.commit()
        session.refresh(character)
        return character


def delete_character(project_id: str, character_id: str) -> None:
    from fastapi import HTTPException

    with project_session(project_id) as session:
        character = session.get(Character, character_id)
        if character is None:
            raise HTTPException(status_code=404, detail="人物不存在")
        session.delete(character)
        session.commit()
