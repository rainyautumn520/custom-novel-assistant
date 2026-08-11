from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    genre: str = ""
    synopsis: str = ""
    target_words: int = 0


class ProjectOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, alias_generator=to_camel, populate_by_name=True
    )

    id: str
    name: str
    genre: str
    synopsis: str
    target_words: int
    status: str
    data_dir: str
    created_at: str
    updated_at: str
