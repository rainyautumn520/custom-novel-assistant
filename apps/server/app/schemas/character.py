from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CharacterCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str = Field(min_length=1, max_length=100)
    aliases: list[str] = []
    identity: str = ""
    personality: str = ""
    appearance: str = ""
    background: str = ""
    goals: str = ""
    tags: list[str] = []
    notes: str = ""
    status: str = "draft"


class CharacterUpdate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str | None = None
    aliases: list[str] | None = None
    identity: str | None = None
    personality: str | None = None
    appearance: str | None = None
    background: str | None = None
    goals: str | None = None
    tags: list[str] | None = None
    notes: str | None = None
    status: str | None = None


class CharacterOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, alias_generator=to_camel, populate_by_name=True
    )

    id: str
    name: str
    aliases: list[str]
    identity: str
    personality: str
    appearance: str
    background: str
    goals: str
    tags: list[str]
    notes: str
    status: str
    created_at: str
    updated_at: str
