from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CoverTaskOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, alias_generator=to_camel, populate_by_name=True
    )

    id: str
    prompt: str
    optimized_prompt: str
    params: dict
    status: str
    idempotency_key: str
    result_path: str | None
    composed_path: str | None
    error: str
    created_at: str
    updated_at: str
