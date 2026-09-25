"""Behaviors for CORS (tech debt 24, DECISIONS.md D36). The web app on Vercel
calls the API on Railway cross-origin with a bearer token, so every request
preflights (Authorization, Content-Type, X-Timezone):
- Given a preflight from an allowed origin, then 200, the origin is echoed,
  GET POST OPTIONS and the three headers are allowed, and no credentials.
- Given a preflight from an unlisted origin, then no allow-origin header.
- Given CORS_ORIGIN_REGEX anchored on the team suffix, then a preview origin
  of ours is allowed and a squatting project name (rizal-ai-evil) is not.
- Given a simple GET with an allowed Origin, then the origin is echoed and
  the response varies on Origin.
"""

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from rizalai.config import get_settings
from rizalai.db.session import get_session
from rizalai.main import create_app

pytestmark = pytest.mark.anyio

LOCAL = "http://localhost:3000"
PREVIEW = "https://rizal-ai-git-feature-jakecob.vercel.app"
# Anchored on the team suffix Vercel appends to preview hostnames, so another
# account's project named rizal-ai-<anything> does not match (D36).
PREVIEW_REGEX = r"https://rizal-ai-[a-z0-9-]+-jakecob\.vercel\.app"
DEFAULT_ORIGINS = "http://localhost:3000,http://127.0.0.1:3000"


def _preflight(origin: str, method: str = "POST") -> dict[str, str]:
    return {
        "Origin": origin,
        "Access-Control-Request-Method": method,
        "Access-Control-Request-Headers": "authorization,content-type,x-timezone",
    }


@pytest.fixture
def fresh_settings(monkeypatch) -> AsyncIterator[None]:
    """Pin the CORS settings to their defaults whatever the developer's shell
    or apps/api/.env says, and clear the cached settings before and after.
    The variables are set, not deleted, because a deleted variable would
    fall back to a value in .env. create_app reads settings once, so every
    test here builds its own app after this runs."""
    monkeypatch.setenv("CORS_ORIGINS", DEFAULT_ORIGINS)
    monkeypatch.setenv("CORS_ORIGIN_REGEX", "")
    get_settings.cache_clear()
    yield
    monkeypatch.undo()
    get_settings.cache_clear()


@pytest.fixture
async def bare_client(fresh_settings) -> AsyncIterator[AsyncClient]:
    """A client over a fresh app with no database: preflights never reach a route."""
    async with AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://test") as client:
        yield client


async def test_preflight_from_allowed_origin(bare_client):
    response = await bare_client.options("/session/anonymous", headers=_preflight(LOCAL))
    assert response.status_code == 200, response.text
    assert response.headers["access-control-allow-origin"] == LOCAL
    methods = {m.strip() for m in response.headers["access-control-allow-methods"].split(",")}
    assert methods == {"GET", "POST", "OPTIONS"}
    allowed = {h.strip().lower() for h in response.headers["access-control-allow-headers"].split(",")}
    assert {"authorization", "content-type", "x-timezone"} <= allowed
    assert "access-control-allow-credentials" not in response.headers


async def test_preflight_from_unlisted_origin_is_not_allowed(bare_client):
    response = await bare_client.options("/tree", headers=_preflight("https://evil.example", "GET"))
    assert "access-control-allow-origin" not in response.headers


async def test_preflight_for_an_unlisted_method_is_rejected(bare_client):
    response = await bare_client.options("/tree", headers=_preflight(LOCAL, "PATCH"))
    assert response.status_code == 400


async def test_regex_allows_preview_origins(monkeypatch, fresh_settings):
    monkeypatch.setenv("CORS_ORIGIN_REGEX", PREVIEW_REGEX)
    get_settings.cache_clear()
    async with AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://test") as client:
        allowed = await client.options("/tree", headers=_preflight(PREVIEW, "GET"))
        other = await client.options("/tree", headers=_preflight("https://someone-else.vercel.app", "GET"))
    assert allowed.status_code == 200, allowed.text
    assert allowed.headers["access-control-allow-origin"] == PREVIEW
    assert "access-control-allow-origin" not in other.headers


async def test_regex_rejects_a_squatting_project_name(monkeypatch, fresh_settings):
    """Anyone can create a Vercel project called rizal-ai-evil; without the
    team suffix in the pattern it would be admitted."""
    monkeypatch.setenv("CORS_ORIGIN_REGEX", PREVIEW_REGEX)
    get_settings.cache_clear()
    async with AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://test") as client:
        response = await client.options(
            "/tree", headers=_preflight("https://rizal-ai-evil.vercel.app", "GET")
        )
    assert "access-control-allow-origin" not in response.headers


async def test_regex_is_off_when_unset(bare_client):
    response = await bare_client.options("/tree", headers=_preflight(PREVIEW, "GET"))
    assert "access-control-allow-origin" not in response.headers


async def test_simple_request_echoes_allowed_origin(db, fresh_settings):
    app = create_app()

    async def _session() -> AsyncIterator:
        yield db

    app.dependency_overrides[get_session] = _session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health", headers={"Origin": LOCAL})
    assert response.status_code == 200, response.text
    assert response.headers["access-control-allow-origin"] == LOCAL
    assert "origin" in response.headers.get("vary", "").lower()
