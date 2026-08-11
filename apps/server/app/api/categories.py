from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.projects import get_app_session
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate
from app.services import category_service, project_service

router = APIRouter(prefix="/api/projects/{project_id}/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(project_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    return category_service.list_categories(project_id)


@router.post("", response_model=CategoryOut, status_code=201)
def create_category(
    project_id: str, payload: CategoryCreate, session: Session = Depends(get_app_session)
):
    project_service.get_project_or_404(session, project_id)
    return category_service.create_category(project_id, payload.model_dump())


@router.put("/{category_id}", response_model=CategoryOut)
def update_category(
    project_id: str,
    category_id: str,
    payload: CategoryUpdate,
    session: Session = Depends(get_app_session),
):
    project_service.get_project_or_404(session, project_id)
    return category_service.update_category(project_id, category_id, payload.model_dump())


@router.delete("/{category_id}", status_code=204)
def delete_category(project_id: str, category_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    category_service.delete_category(project_id, category_id)
