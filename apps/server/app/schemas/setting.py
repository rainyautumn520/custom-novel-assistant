from pydantic import BaseModel, ConfigDict, Field


class SettingCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    category_id: str | None = None
    content_md: str = ""
    tags: list[str] = []
    status: str = "draft"


class SettingUpdate(BaseModel):
    title: str | None = None
    category_id: str | None = None
    content_md: str | None = None
    tags: list[str] | None = None
    status: str | None = None


class SettingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    category_id: str | None
    title: str
    content_md: str
    tags: list[str]
    status: str
    created_at: str
    updated_at: str
