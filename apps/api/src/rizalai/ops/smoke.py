"""`rizalai smoke`: check a running API the way the web app uses it (plan 007).

Each check is one request, reported as pass or fail with the detail, in the
order a first visit makes them: health, the CORS preflight from the web
origin, an anonymous session, the learner, the tree, and the first published
lesson with its passages. Later checks need the token, so a failed session
fails them too, with that reason. A body that is not JSON, or JSON of an
unexpected shape (for example the web app's page when --base-url points at
it), is a failed check with the detail, never a traceback.
"""

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


class BadBodyError(Exception):
    """The response was not the JSON shape the check expects."""


def _json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except ValueError as err:
        raise BadBodyError(f"HTTP {response.status_code}, not JSON: {response.text.strip()[:120]!r}") from err


def _detail(response: httpx.Response) -> str:
    body = response.text.strip().replace("\n", " ")
    return f"HTTP {response.status_code}" + (f": {body[:160]}" if body else "")


async def run_smoke(client: httpx.AsyncClient, origin: str, expect_lessons: int | None = None) -> list[Check]:
    checks: list[Check] = []
    headers = {"Origin": origin, "X-Timezone": "Asia/Manila"}

    async def attempt(name: str, method: str, url: str, **kwargs: Any) -> httpx.Response | None:
        try:
            return await client.request(method, url, **kwargs)
        except httpx.HTTPError as err:
            checks.append(Check(name, False, f"{type(err).__name__}: {err}"))
            return None

    response = await attempt("GET /health", "GET", "/health")
    if response is not None:
        checks.append(Check("GET /health", response.status_code == 200, _detail(response)))

    name = "OPTIONS /tree (preflight)"
    response = await attempt(
        name,
        "OPTIONS",
        "/tree",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,content-type,x-timezone",
        },
    )
    if response is not None:
        allowed = response.headers.get("access-control-allow-origin")
        ok = response.status_code == 200 and allowed == origin
        checks.append(Check(name, ok, f"HTTP {response.status_code}, allow-origin {allowed or 'missing'}"))

    token: str | None = None
    name = "POST /session/anonymous"
    response = await attempt(name, "POST", "/session/anonymous", headers=headers)
    if response is not None:
        try:
            body = _json(response) if response.status_code in (200, 201) else None
            issued = body.get("access_token") if isinstance(body, dict) else None
        except BadBodyError as err:
            checks.append(Check(name, False, str(err)))
        else:
            if isinstance(issued, str) and issued:
                token = issued
                checks.append(Check(name, True, f"HTTP {response.status_code}, token issued"))
            else:
                checks.append(Check(name, False, _detail(response)))

    authed = {**headers, "Authorization": f"Bearer {token}"}
    later = ["GET /me", "GET /tree", "GET /lessons/{first published}"]
    if token is None:
        checks += [Check(n, False, "skipped: no session token") for n in later]
        return checks

    response = await attempt("GET /me", "GET", "/me", headers=authed)
    if response is not None:
        checks.append(Check("GET /me", response.status_code == 200, _detail(response)))

    first: str | None = None
    response = await attempt("GET /tree", "GET", "/tree", headers=authed)
    if response is not None:
        if response.status_code != 200:
            checks.append(Check("GET /tree", False, _detail(response)))
        else:
            try:
                tree = _json(response)
                lessons = [lesson for unit in tree["units"] for lesson in unit["lessons"]]
                first = next((str(les["id"]) for les in lessons if les["status"] != "locked"), None)
            except BadBodyError as err:
                checks.append(Check("GET /tree", False, str(err)))
            except (KeyError, TypeError) as err:
                checks.append(Check("GET /tree", False, f"unexpected shape ({type(err).__name__}: {err})"))
            else:
                ok = expect_lessons is None or len(lessons) == expect_lessons
                wanted = "" if ok or expect_lessons is None else f", expected {expect_lessons}"
                checks.append(Check("GET /tree", ok and first is not None, f"{len(lessons)} lessons{wanted}"))

    name = "GET /lessons/{first published}"
    if first is None:
        checks.append(Check(name, False, "skipped: no published lesson on the tree"))
        return checks
    response = await attempt(name, "GET", f"/lessons/{first}", headers=authed)
    if response is not None:
        if response.status_code != 200:
            checks.append(Check(name, False, _detail(response)))
        else:
            try:
                body = _json(response)
                passages = len(body["source_passage_ids"])
                checks.append(Check(name, passages > 0, f"{body.get('slug')}: {passages} passages"))
            except BadBodyError as err:
                checks.append(Check(name, False, str(err)))
            except (KeyError, TypeError, AttributeError) as err:
                checks.append(Check(name, False, f"unexpected shape ({type(err).__name__}: {err})"))
    return checks


def format_checks(checks: list[Check]) -> str:
    width = max((len(c.name) for c in checks), default=0)
    rows = [f"{'PASS' if c.ok else 'FAIL'}  {c.name:<{width}}  {c.detail}" for c in checks]
    failed = sum(not c.ok for c in checks)
    rows.append("smoke ok" if not failed else f"smoke FAILED: {failed} of {len(checks)} checks")
    return "\n".join(rows)
