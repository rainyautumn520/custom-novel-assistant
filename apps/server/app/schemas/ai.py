from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class AiSessionCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    title: str = Field(default="新讨论", max_length=200)


class AiSessionOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, alias_generator=to_camel, populate_by_name=True
    )

    id: str
    title: str
    created_at: str
    updated_at: str


class AiMessageOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, alias_generator=to_camel, populate_by_name=True
    )

    id: str
    session_id: str
    role: str
    content: str
    sources: list[str]
    created_at: str


class AiChatRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    content: str = Field(min_length=1)


class AiChatReply(BaseModel):
    reply: str


class AiPromptUpdate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    prompt: str = ""
