from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from sqlalchemy.orm import Session

from app.api.projects import get_app_session
from app.schemas.link import EntityLinkOut
from app.services import link_service, project_service

router = APIRouter(prefix="/api/projects/{project_id}", tags=["links"])


class CharacterLinksRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    setting_ids: list[str] = []


class CreateLinkRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    source_type: str
    source_id: str
    target_type: str
    target_id: str
    relation_type: str = "refers_to"


@router.get("/characters/{character_id}/links", response_model=list[EntityLinkOut])
def list_character_links(
    project_id: str, character_id: str, session: Session = Depends(get_app_session)
):
    project_service.get_project_or_404(session, project_id)
    return link_service.list_links_for(project_id, "character", character_id)


@router.put("/characters/{character_id}/links", response_model=list[EntityLinkOut])
def replace_character_links(
    project_id: str,
    character_id: str,
    payload: CharacterLinksRequest,
    session: Session = Depends(get_app_session),
):
    project_service.get_project_or_404(session, project_id)
    return link_service.replace_setting_links(project_id, character_id, payload.setting_ids)


@router.post("/links", response_model=EntityLinkOut, status_code=201)
def create_link(
    project_id: str, payload: CreateLinkRequest, session: Session = Depends(get_app_session)
):
    project_service.get_project_or_404(session, project_id)
    return link_service.create_link(project_id, payload.model_dump())


@router.delete("/links/{link_id}", status_code=204)
def delete_link(project_id: str, link_id: str, session: Session = Depends(get_app_session)):
    project_service.get_project_or_404(session, project_id)
    link_service.delete_link(project_id, link_id)
