from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class OutlineCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    level: str = Field(pattern="^(volume|chapter|beat)$")
    parent_id: str | None = None
    title: str = Field(min_length=1, max_length=200)
    goal: str = ""
    must_cover: list[str] = []
    forbidden: list[str] = []
    target_words: int = 0
    sort_order: int = 0


class OutlineUpdate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    parent_id: str | None = None
    title: str | None = None
    goal: str | None = None
    must_cover: list[str] | None = None
    forbidden: list[str] | None = None
    status: str | None = None
    target_words: int | None = None
    sort_order: int | None = None


class OutlineOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, alias_generator=to_camel, populate_by_name=True
    )

    id: str
    parent_id: str | None
    level: str
    sort_order: int
    title: str
    goal: str
    must_cover: list[str]
    forbidden: list[str]
    status: str
    target_words: int
    chapter_id: str | None
    created_at: str
    updated_at: str
