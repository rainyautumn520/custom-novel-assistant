from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class AssetCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    title: str = Field(min_length=1, max_length=200)
    kind: str = "text"
    content_md: str = ""
    source: str = ""
    tags: list[str] = []
    notes: str = ""


class AssetUpdate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    title: str | None = None
    kind: str | None = None
    content_md: str | None = None
    source: str | None = None
    tags: list[str] | None = None
    notes: str | None = None


class AssetOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, alias_generator=to_camel, populate_by_name=True
    )

    id: str
    title: str
    kind: str
    content_md: str
    file_path: str | None
    source: str
    tags: list[str]
    notes: str
    created_at: str
    updated_at: str
