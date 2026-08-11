from sqlalchemy import select

from app.core.database import project_session
from app.models.chekhov import Chekhov


def list_chekhovs(project_id: str) -> list[Chekhov]:
    with project_session(project_id) as session:
        return list(
            session.scalars(
                select(Chekhov).order_by(
                    Chekhov.status, Chekhov.created_at.desc()
                )
            )
        )


def create_chekhov(project_id: str, data: dict) -> Chekhov:
    with project_session(project_id) as session:
        item = Chekhov(**data)
        session.add(item)
        session.commit()
        session.refresh(item)
        return item


def update_chekhov(project_id: str, chekhov_id: str, data: dict) -> Chekhov:
    from fastapi import HTTPException

    with project_session(project_id) as session:
        item = session.get(Chekhov, chekhov_id)
        if item is None:
            raise HTTPException(status_code=404, detail="伏笔不存在")
        for key, value in data.items():
            if value is not None:
                setattr(item, key, value)
        session.commit()
        session.refresh(item)
        return item


def delete_chekhov(project_id: str, chekhov_id: str) -> None:
    from fastapi import HTTPException

    with project_session(project_id) as session:
        item = session.get(Chekhov, chekhov_id)
        if item is None:
            raise HTTPException(status_code=404, detail="伏笔不存在")
        session.delete(item)
        session.commit()
