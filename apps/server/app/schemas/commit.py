from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ChapterCommitOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, alias_generator=to_camel, populate_by_name=True
    )

    id: str
    chapter_id: str
    status: str
    accepted_events: list
    state_deltas: dict
    entity_deltas: list
    summary_text: str
    projection_status: dict
    created_at: str


class ChapterCommitListOut(ChapterCommitOut):
    chapter_title: str = ""
