from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ChekhovCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    planted_chapter_id: str | None = None
    payoff_chapter_id: str | None = None
    status: str = "open"


class ChekhovUpdate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    title: str | None = None
    description: str | None = None
    planted_chapter_id: str | None = None
    payoff_chapter_id: str | None = None
    status: str | None = None


class ChekhovOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, alias_generator=to_camel, populate_by_name=True
    )

    id: str
    title: str
    description: str
    planted_chapter_id: str | None
    payoff_chapter_id: str | None
    status: str
    created_at: str
    updated_at: str
