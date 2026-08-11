from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置。环境变量前缀：AI_NOVEL_。"""

    data_dir: Path = Path.home() / "ai-novel-ide-data"
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"
    seedream_api_key: str = ""
    seedream_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    seedream_model: str = "doubao-seedream-5-0-260128"
    vector_backend: str = "sentence-transformers"  # sentence-transformers | ollama
    vector_model: str = "BAAI/bge-small-zh-v1.5"  # 或 ollama 的 bge-m3
    ollama_base_url: str = "http://localhost:11434"

    model_config = SettingsConfigDict(
        env_prefix="AI_NOVEL_",
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
