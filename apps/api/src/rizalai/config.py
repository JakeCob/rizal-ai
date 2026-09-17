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

    # Sessions (D33): the API issues HS256 tokens with this secret. AUTH_JWKS_URL is
    # the hook for a future identity provider; SUPABASE_JWT_SECRET is honored for
    # one release so a rollback is an env change.
    session_jwt_secret: str = ""
    auth_jwks_url: str = ""
    supabase_jwt_secret: str = ""

    content_dir: Path = Path("../../content")

    embeddings_provider: Literal["fake", "deepinfra"] = "fake"
    embeddings_api_key: str = ""
    embeddings_model: str = "BAAI/bge-m3"

    # Audio (D12, D33): local directory or an S3-compatible bucket (Railway buckets).
    audio_store: Literal["local", "s3"] = "local"
    audio_local_dir: Path = Path("data/audio")
    audio_base_url: str = "http://localhost:8000/audio"
    s3_endpoint_url: str = ""
    s3_bucket: str = "audio"
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_region: str = "auto"
    tts_engine: str = "fake"
    xtts_speaker_wav: str = ""

    # LLM (D09, D32). openrouter is production; the model default depends on the provider.
    llm_provider: Literal["fake", "openrouter", "anthropic"] = "fake"
    llm_model: str = ""
    openrouter_api_key: str = ""
    anthropic_api_key: str = ""

    @property
    def active_database_url(self) -> str:
        return self.test_database_url if self.env == "test" else self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
