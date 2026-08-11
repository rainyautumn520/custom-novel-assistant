from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ChapterCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    title: str = Field(min_length=1, max_length=200)
    outline_node_id: str | None = None


class ChapterUpdate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    title: str | None = None
    content_md: str | None = None


class ChapterOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, alias_generator=to_camel, populate_by_name=True
    )

    id: str
    title: str
    outline_node_id: str | None
    word_count: int
    file_path: str
    file_hash: str
    status: str
    created_at: str
    updated_at: str


class ChapterDetail(ChapterOut):
    content_md: str = ""
