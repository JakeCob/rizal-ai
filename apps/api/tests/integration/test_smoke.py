"""Behaviors for `rizalai smoke` (plan 007): against a running API and the
web origin, it checks /health, a CORS preflight from the origin, POST
/session/anonymous, GET /me, GET /tree and GET /lessons/{first published},
reports each as pass or fail with the detail, and fails the run when any
check fails. Here it runs against the ASGI app through httpx.
- Given a body that is not JSON or has an unexpected shape, then that check
  fails with the detail and the run still reports every check.
- Given the preflight, then it asks for the three headers the web app sends.
"""

from pathlib import Path

import httpx
import pytest

from rizalai.content.seed import seed_content
from rizalai.corpus.gutenberg import EDITIONS
from rizalai.corpus.ingest import ingest_text
from rizalai.ops.smoke import format_checks, run_smoke

pytestmark = pytest.mark.anyio

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
CONTENT_DIR = FIXTURES / "content"
ORIGIN = "http://localhost:3000"


async def _seed_with_passages(db) -> None:
    for key in ("noli_es", "noli_tl"):
        raw = (FIXTURES / "gutenberg" / f"{key}.txt").read_text(encoding="utf-8")
        await ingest_text(db, EDITIONS[key], raw, embedder=None)
    await seed_content(db, CONTENT_DIR)


async def test_every_check_passes_against_a_seeded_api(client, db):
    await _seed_with_passages(db)
    checks = await run_smoke(client, ORIGIN, expect_lessons=4)
    assert [c.name for c in checks] == [
        "GET /health",
        "OPTIONS /tree (preflight)",
        "POST /session/anonymous",
        "GET /me",
        "GET /tree",
        "GET /lessons/{first published}",
    ]
    assert all(c.ok for c in checks), format_checks(checks)
    assert "PASS" in format_checks(checks)


class FailTree(httpx.AsyncBaseTransport):
    """Delegates to the app, except that GET /tree returns a 500."""

    def __init__(self, inner: httpx.AsyncBaseTransport) -> None:
        self.inner = inner

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        if request.method == "GET" and request.url.path == "/tree":
            return httpx.Response(500, text="Internal Server Error")
        return await self.inner.handle_async_request(request)


async def test_a_failing_endpoint_is_reported_with_its_detail(client, db):
    await seed_content(db, CONTENT_DIR)
    broken = httpx.AsyncClient(transport=FailTree(client._transport), base_url="http://test")
    checks = await run_smoke(broken, ORIGIN)
    by_name = {c.name: c for c in checks}
    assert not by_name["GET /tree"].ok
    assert "500" in by_name["GET /tree"].detail
    assert by_name["GET /health"].ok
    assert "FAIL" in format_checks(checks)


async def test_a_wrong_lesson_count_fails(client, db):
    await seed_content(db, CONTENT_DIR)
    checks = await run_smoke(client, ORIGIN, expect_lessons=8)
    tree = next(c for c in checks if c.name == "GET /tree")
    assert not tree.ok and "4 lessons" in tree.detail


async def test_an_unlisted_origin_fails_the_preflight(client, db):
    checks = await run_smoke(client, "https://evil.example")
    preflight = next(c for c in checks if c.name.startswith("OPTIONS"))
    assert not preflight.ok


class Rewrite(httpx.AsyncBaseTransport):
    """Delegates to the app, except for one path whose response is replaced."""

    def __init__(self, inner: httpx.AsyncBaseTransport, path: str, response: httpx.Response) -> None:
        self.inner, self.path, self.response = inner, path, response
        self.seen: list[httpx.Request] = []

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.seen.append(request)
        if request.method != "OPTIONS" and request.url.path == self.path:
            return self.response
        return await self.inner.handle_async_request(request)


@pytest.mark.parametrize(
    ("path", "response", "failed"),
    [
        ("/tree", httpx.Response(200, text="<html>not the API</html>"), "GET /tree"),
        ("/tree", httpx.Response(200, json={"not_units": []}), "GET /tree"),
        (
            "/session/anonymous",
            httpx.Response(201, text="<html>proxy page</html>"),
            "POST /session/anonymous",
        ),
        ("/health", httpx.Response(200, text="ok"), None),
    ],
    ids=["tree-html", "tree-shape", "session-html", "health-text"],
)
async def test_bad_bodies_become_failed_checks(client, db, path, response, failed):
    await _seed_with_passages(db)
    transport = Rewrite(client._transport, path, response)
    broken = httpx.AsyncClient(transport=transport, base_url="http://test")
    checks = await run_smoke(broken, ORIGIN)  # must not raise
    assert len(checks) == 6
    if failed is not None:
        check = next(c for c in checks if c.name == failed)
        assert not check.ok and check.detail


async def test_the_preflight_asks_for_the_web_apps_headers(client, db):
    transport = Rewrite(client._transport, "/never", httpx.Response(200))
    await run_smoke(httpx.AsyncClient(transport=transport, base_url="http://test"), ORIGIN)
    preflight = next(r for r in transport.seen if r.method == "OPTIONS")
    asked = {h.strip() for h in preflight.headers["access-control-request-headers"].split(",")}
    assert asked == {"authorization", "content-type", "x-timezone"}
