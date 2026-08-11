from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CategoryCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str = Field(min_length=1, max_length=100)
    parent_id: str | None = None
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str | None = None
    parent_id: str | None = None
    sort_order: int | None = None


class CategoryOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, alias_generator=to_camel, populate_by_name=True
    )

    id: str
    parent_id: str | None
    name: str
    sort_order: int
    created_at: str
    updated_at: str
