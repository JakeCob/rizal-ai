"""Application settings, loaded from the environment or a .env file."""

from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProductionConfigError(RuntimeError):
    """A setting the API needs in production is missing. Raised at app
    creation so a deploy fails its healthcheck instead of serving and then
    failing on the first request that needs the setting (D37)."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: Literal["local", "test", "ci", "production"] = "local"
    # Injected by Railway into every service. With ENV unset it means
    # production; with ENV set to anything else the API refuses to start (D37).
    railway_environment: str | None = None

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/rizalai"
    test_database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/rizalai_test"

    # Sessions (D33): the API issues HS256 tokens with this secret. AUTH_JWKS_URL is
    # the hook for a future identity provider; SUPABASE_JWT_SECRET is honored for
    # one release so a rollback is an env change.
    session_jwt_secret: str = ""
    auth_jwks_url: str = ""
    supabase_jwt_secret: str = ""

    # CORS (tech debt 24, D36): comma-separated web origins allowed to call the API
    # from a browser. Production: the Vercel URL. CORS_ORIGIN_REGEX optionally admits
    # Vercel preview hostnames. Bearer tokens only, so no credentials. A string, not a
    # list: pydantic-settings would JSON-decode a list from the environment.
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    cors_origin_regex: str | None = None

    content_dir: Path = Path("../../content")

    embeddings_provider: Literal["fake", "deepinfra"] = "fake"
    embeddings_api_key: str = ""
    embeddings_model: str = "BAAI/bge-m3"

    # Audio (D12, D33): local directory or an S3-compatible bucket (Railway buckets).
    audio_store: Literal["local", "s3"] = "local"
    audio_local_dir: Path = Path("data/audio")
    audio_base_url: str = "http://localhost:8000/audio"
    s3_endpoint_url: str = ""
    s3_bucket: str = ""  # a Railway bucket's real name is its display name plus a hash
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

    @model_validator(mode="after")
    def _railway_means_production(self) -> "Settings":
        if self.railway_environment and "env" not in self.model_fields_set:
            self.env = "production"
        return self

    @field_validator("database_url", "test_database_url")
    @classmethod
    def _asyncpg_scheme(cls, value: str) -> str:
        # Railway hands out postgresql:// (and some tools postgres://); asyncpg
        # is the only driver installed, so rewrite the scheme rather than fail.
        for prefix in ("postgresql://", "postgres://"):
            if value.startswith(prefix):
                return "postgresql+asyncpg://" + value[len(prefix) :]
        return value

    @field_validator("cors_origin_regex")
    @classmethod
    def _blank_regex_is_none(cls, value: str | None) -> str | None:
        # The .env examples ship CORS_ORIGIN_REGEX= (blank), which must mean no regex.
        return value if value and value.strip() else None

    @property
    def active_database_url(self) -> str:
        return self.test_database_url if self.env == "test" else self.database_url

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.cors_origins.split(",") if o.strip()]

    def validate_for_production(self) -> None:
        """Refuse to start in production without the settings the API needs,
        naming each one. A local default counts as missing: an origin list
        that is only localhost, a database or audio URL on localhost, an
        LLM_PROVIDER left to its default. A no-op outside production, except
        that Railway with a non-production ENV is refused outright."""
        if self.railway_environment and self.env != "production":
            raise ProductionConfigError(
                f"RAILWAY_ENVIRONMENT is set ({self.railway_environment}) but ENV={self.env}: "
                "set ENV=production on the service, or unset ENV"
            )
        if self.env != "production":
            return
        missing = []
        if not self.session_jwt_secret.strip():
            missing.append("SESSION_JWT_SECRET")
        if not [o for o in self.cors_origin_list if not _is_local(urlsplit(o).hostname)]:
            missing.append("CORS_ORIGINS")
        if _is_local(_database_host(self.database_url)):
            missing.append("DATABASE_URL")
        if self.audio_store == "s3":
            s3 = {
                "S3_ENDPOINT_URL": self.s3_endpoint_url,
                "S3_BUCKET": self.s3_bucket,
                "S3_ACCESS_KEY_ID": self.s3_access_key_id,
                "S3_SECRET_ACCESS_KEY": self.s3_secret_access_key,
            }
            missing += [name for name, value in s3.items() if not value.strip()]
            if not self.audio_base_url.strip() or _is_local(urlsplit(self.audio_base_url).hostname):
                missing.append("AUDIO_BASE_URL")
        if "llm_provider" not in self.model_fields_set:
            missing.append("LLM_PROVIDER (write it out; fake is allowed)")
        elif self.llm_provider == "openrouter" and not self.openrouter_api_key.strip():
            missing.append("OPENROUTER_API_KEY")
        elif self.llm_provider == "anthropic" and not self.anthropic_api_key.strip():
            missing.append("ANTHROPIC_API_KEY")
        if missing:
            raise ProductionConfigError(
                f"ENV=production but these settings are unset, blank or local: {', '.join(missing)}"
            )


LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1", "0.0.0.0"})  # noqa: S104, a list of hosts to refuse


def _is_local(host: str | None) -> bool:
    return host is None or host.lower() in LOCAL_HOSTS


def _database_host(url: str) -> str | None:
    from sqlalchemy.engine import make_url
    from sqlalchemy.exc import ArgumentError

    try:
        return make_url(url).host
    except ArgumentError:
        return None


@lru_cache
def get_settings() -> Settings:
    return Settings()
