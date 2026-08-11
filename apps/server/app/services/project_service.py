from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import AppSession, ensure_project_db, new_id, settings
from app.models.app import Project


def create_project(name: str, genre: str = "", synopsis: str = "", target_words: int = 0) -> Project:
    from fastapi import HTTPException

    name = name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="书名去除首尾空格后不得为空")

    project_id = new_id()
    project_dir = settings.data_dir / "workspaces" / project_id
    ensure_project_db(project_id)
    with AppSession() as session:
        project = Project(
            id=project_id,
            name=name,
            genre=genre,
            synopsis=synopsis,
            target_words=target_words,
            data_dir=str(project_dir),
        )
        session.add(project)
        session.commit()
        session.refresh(project)
        return project


def list_projects() -> list[Project]:
    with AppSession() as session:
        return list(session.scalars(select(Project).order_by(Project.updated_at.desc())))


def get_project_or_404(session: Session, project_id: str) -> Project:
    project = session.get(Project, project_id)
    if project is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="作品不存在")
    return project
