from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置。环境变量前缀：AI_NOVEL_。"""

    data_dir: Path = Path.home() / "ai-novel-ide-data"
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    model_config = SettingsConfigDict(env_prefix="AI_NOVEL_")


settings = Settings()
