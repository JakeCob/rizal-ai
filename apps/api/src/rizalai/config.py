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

    audio_store: Literal["local", "supabase"] = "local"
    audio_local_dir: Path = Path("data/audio")
    audio_base_url: str = "http://localhost:8000/audio"
    audio_bucket: str = "audio"
    supabase_service_role_key: str = ""
    tts_engine: str = "fake"
    xtts_speaker_wav: str = ""

    llm_provider: Literal["fake", "anthropic"] = "fake"
    llm_model: str = "claude-opus-5"
    anthropic_api_key: str = ""

    @property
    def active_database_url(self) -> str:
        return self.test_database_url if self.env == "test" else self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
