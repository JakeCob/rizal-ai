"""Behaviors for the CORS settings (tech debt 24, DECISIONS.md D36):
- Given CORS_ORIGINS unset, then the allowed origins are the two local web
  origins.
- Given a comma-separated CORS_ORIGINS with spaces, a trailing slash and a
  trailing comma, then the list holds the trimmed origins only.
- Given CORS_ORIGIN_REGEX unset or blank (as the .env examples ship it), then
  no regex applies.
- Given DATABASE_URL in Railway's postgresql:// or postgres:// form, then it
  becomes postgresql+asyncpg:// (the only driver installed); an asyncpg URL is
  left alone (plan 007, D37).
- Given ENV=production, when a setting the API needs is unset, blank, or still
  its local default, then startup is refused with a message naming the
  variable: SESSION_JWT_SECRET, CORS_ORIGINS (localhost-only counts as
  missing), DATABASE_URL (localhost counts as missing), LLM_PROVIDER (must be
  written out; fake is allowed), the four S3 settings and AUDIO_BASE_URL under
  AUDIO_STORE=s3, and the key of the chosen LLM provider. Given ENV=local, the
  same settings load and start fine.
- Given Railway's RAILWAY_ENVIRONMENT with ENV unset, then the API runs as
  production; with ENV set to anything else, it refuses to start.
"""

import pytest

from rizalai.config import ProductionConfigError, Settings, get_settings


def _settings(monkeypatch, **env: str) -> Settings:
    for name in ("CORS_ORIGINS", "CORS_ORIGIN_REGEX"):
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    return Settings(_env_file=None)  # type: ignore[call-arg]


def test_default_origins_are_the_local_web_app(monkeypatch):
    assert _settings(monkeypatch).cors_origin_list == ["http://localhost:3000", "http://127.0.0.1:3000"]


def test_origins_are_trimmed_and_empty_entries_dropped(monkeypatch):
    settings = _settings(monkeypatch, CORS_ORIGINS=" https://rizal.vercel.app/ ,https://b.example,")
    assert settings.cors_origin_list == ["https://rizal.vercel.app", "https://b.example"]


def test_origin_regex_is_off_by_default(monkeypatch):
    assert _settings(monkeypatch).cors_origin_regex is None


def test_origin_regex_is_read_from_the_environment(monkeypatch):
    pattern = r"https://rizal-ai-[a-z0-9-]+\.vercel\.app"
    assert _settings(monkeypatch, CORS_ORIGIN_REGEX=pattern).cors_origin_regex == pattern


def test_blank_origin_regex_means_none(monkeypatch):
    assert _settings(monkeypatch, CORS_ORIGIN_REGEX="").cors_origin_regex is None
    assert _settings(monkeypatch, CORS_ORIGIN_REGEX="   ").cors_origin_regex is None


PRODUCTION = {
    "ENV": "production",
    "DATABASE_URL": "postgresql+asyncpg://u:p@db.internal:5432/rizalai",
    "SESSION_JWT_SECRET": "a" * 64,
    "CORS_ORIGINS": "https://rizal-ai.vercel.app",
    "AUDIO_STORE": "s3",
    "S3_ENDPOINT_URL": "https://storage.example",
    "S3_BUCKET": "audio-abc123",
    "S3_ACCESS_KEY_ID": "key",
    "S3_SECRET_ACCESS_KEY": "secret",
    "AUDIO_BASE_URL": "https://api.example/audio",
    "LLM_PROVIDER": "openrouter",
    "OPENROUTER_API_KEY": "sk-test",
}


def _env(monkeypatch, drop: tuple[str, ...] = (), **overrides: str) -> Settings:
    """Settings from exactly these variables: every setting's variable and
    RAILWAY_ENVIRONMENT are cleared first, no .env file is read, and names in
    `drop` are left unset."""
    for name in [*(f.upper() for f in Settings.model_fields), "RAILWAY_ENVIRONMENT"]:
        monkeypatch.delenv(name, raising=False)
    for name, value in {**PRODUCTION, **overrides}.items():
        if name not in drop:
            monkeypatch.setenv(name, value)
    return Settings(_env_file=None)  # type: ignore[call-arg]


@pytest.mark.parametrize(
    "given",
    ["postgresql://u:p@h:5432/db", "postgres://u:p@h:5432/db", "postgresql+asyncpg://u:p@h:5432/db"],
    ids=["postgresql", "postgres", "asyncpg"],
)
def test_database_url_is_rewritten_to_asyncpg(monkeypatch, given):
    settings = _env(monkeypatch, DATABASE_URL=given, TEST_DATABASE_URL=given)
    assert settings.database_url == "postgresql+asyncpg://u:p@h:5432/db"
    assert settings.test_database_url == "postgresql+asyncpg://u:p@h:5432/db"


def test_complete_production_settings_pass(monkeypatch):
    _env(monkeypatch).validate_for_production()


REQUIRED = [
    "SESSION_JWT_SECRET",
    "CORS_ORIGINS",
    "DATABASE_URL",
    "S3_ENDPOINT_URL",
    "S3_BUCKET",
    "S3_ACCESS_KEY_ID",
    "S3_SECRET_ACCESS_KEY",
    "AUDIO_BASE_URL",
    "OPENROUTER_API_KEY",
    "LLM_PROVIDER",
]


@pytest.mark.parametrize("variable", REQUIRED)
def test_production_refuses_an_unset_setting(monkeypatch, variable):
    settings = _env(monkeypatch, drop=(variable,))
    with pytest.raises(ProductionConfigError, match=variable):
        settings.validate_for_production()


@pytest.mark.parametrize("variable", [v for v in REQUIRED if v not in ("LLM_PROVIDER", "DATABASE_URL")])
def test_production_refuses_a_blank_setting(monkeypatch, variable):
    settings = _env(monkeypatch, **{variable: ""})
    with pytest.raises(ProductionConfigError, match=variable):
        settings.validate_for_production()


@pytest.mark.parametrize(
    ("variable", "local_value"),
    [
        ("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"),
        ("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/rizalai"),
        ("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1/rizalai"),
        ("AUDIO_BASE_URL", "http://localhost:8000/audio"),
    ],
)
def test_production_refuses_local_values(monkeypatch, variable, local_value):
    settings = _env(monkeypatch, **{variable: local_value})
    with pytest.raises(ProductionConfigError, match=variable):
        settings.validate_for_production()


def test_production_accepts_the_fake_llm_when_written_out(monkeypatch):
    """The first deploy runs without an OpenRouter key (docs/deploy.md)."""
    _env(monkeypatch, drop=("OPENROUTER_API_KEY",), LLM_PROVIDER="fake").validate_for_production()


def test_anthropic_needs_its_key(monkeypatch):
    settings = _env(monkeypatch, LLM_PROVIDER="anthropic")
    with pytest.raises(ProductionConfigError, match="ANTHROPIC_API_KEY"):
        settings.validate_for_production()
    _env(monkeypatch, LLM_PROVIDER="anthropic", ANTHROPIC_API_KEY="sk-ant").validate_for_production()


def test_embeddings_are_not_checked(monkeypatch):
    """Embeddings are CLI only, so the API does not require their key."""
    _env(monkeypatch, EMBEDDINGS_PROVIDER="deepinfra").validate_for_production()


def test_s3_and_openrouter_settings_are_needed_only_when_chosen(monkeypatch):
    settings = _env(
        monkeypatch,
        drop=("S3_BUCKET", "S3_ACCESS_KEY_ID", "AUDIO_BASE_URL", "OPENROUTER_API_KEY"),
        AUDIO_STORE="local",
        LLM_PROVIDER="fake",
    )
    settings.validate_for_production()


def test_local_loads_with_the_same_gaps(monkeypatch):
    settings = _env(
        monkeypatch, drop=("SESSION_JWT_SECRET", "CORS_ORIGINS", "DATABASE_URL", "LLM_PROVIDER"), ENV="local"
    )
    settings.validate_for_production()  # a no-op outside production


def test_railway_without_env_runs_as_production(monkeypatch):
    settings = _env(monkeypatch, drop=("ENV",), RAILWAY_ENVIRONMENT="production")
    assert settings.env == "production"
    settings.validate_for_production()

    missing = _env(monkeypatch, drop=("ENV", "SESSION_JWT_SECRET"), RAILWAY_ENVIRONMENT="production")
    with pytest.raises(ProductionConfigError, match="SESSION_JWT_SECRET"):
        missing.validate_for_production()


@pytest.mark.parametrize("env", ["local", "test", "ci"])
def test_railway_with_a_non_production_env_refuses_to_start(monkeypatch, env):
    settings = _env(monkeypatch, ENV=env, RAILWAY_ENVIRONMENT="production")
    with pytest.raises(ProductionConfigError, match="RAILWAY_ENVIRONMENT"):
        settings.validate_for_production()


def test_s3_bucket_has_no_default(monkeypatch):
    monkeypatch.delenv("S3_BUCKET", raising=False)
    assert Settings(_env_file=None).s3_bucket == ""  # type: ignore[call-arg]


def test_create_app_refuses_to_start_in_production_without_a_secret(monkeypatch):
    from rizalai.main import create_app

    _env(monkeypatch, drop=("SESSION_JWT_SECRET",))
    get_settings.cache_clear()
    try:
        with pytest.raises(ProductionConfigError, match="SESSION_JWT_SECRET"):
            create_app()
    finally:
        monkeypatch.undo()
        get_settings.cache_clear()
