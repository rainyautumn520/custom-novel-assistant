from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class EntityLinkOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, alias_generator=to_camel, populate_by_name=True
    )

    id: str
    source_type: str
    source_id: str
    target_type: str
    target_id: str
    relation_type: str
    created_at: str
