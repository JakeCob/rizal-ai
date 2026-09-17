"""Application settings, loaded from the environment or a .env file."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: Literal["local", "test", "ci", "production"] = "local"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/rizalai"
    test_database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/rizalai_test"

    supabase_url: str = ""
    supabase_jwt_secret: str = ""

    content_dir: Path = Path("../../content")

    embeddings_provider: Literal["fake", "deepinfra"] = "fake"
    embeddings_api_key: str = ""
    embeddings_model: str = "BAAI/bge-m3"

    anthropic_api_key: str = ""

    @property
    def active_database_url(self) -> str:
        return self.test_database_url if self.env == "test" else self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
