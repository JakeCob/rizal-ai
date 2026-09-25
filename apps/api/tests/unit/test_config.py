"""Behaviors for the CORS settings (tech debt 24, DECISIONS.md D36):
- Given CORS_ORIGINS unset, then the allowed origins are the two local web
  origins.
- Given a comma-separated CORS_ORIGINS with spaces, a trailing slash and a
  trailing comma, then the list holds the trimmed origins only.
- Given CORS_ORIGIN_REGEX unset or blank (as the .env examples ship it), then
  no regex applies.
"""

from rizalai.config import Settings


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
