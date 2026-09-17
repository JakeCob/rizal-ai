"""Behaviors for GET /lessons/{id}/reflection (SPEC.md 6.4, 6.7):
- first request generates once, validates, caches, and returns published
- second request makes no LLM call
- a draft whose span is not verbatim is regenerated once, then falls back
- the response carries the three labeled passage layers
- a rejected cache row regenerates on the next request
- 401 without auth, 404 unknown lesson
"""

import uuid
from pathlib import Path

import pytest
from sqlalchemy import select

from rizalai.content.loader import lesson_id
from rizalai.content.seed import seed_content
from rizalai.corpus.gutenberg import EDITIONS
from rizalai.corpus.ingest import ingest_text
from rizalai.db.models import GeneratedContentCache, SourcePassage
from rizalai.generation.llm import FakeLLMClient, get_llm_client
from rizalai.generation.service import reject_reflection
from tests.helpers import mint_token

pytestmark = pytest.mark.anyio

CONTENT_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "content"
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "gutenberg"
LESSON = lesson_id("scaffold-placeholder")


async def _prepare(db):
    for key in ("noli_es", "noli_tl", "noli_en"):
        await ingest_text(
            db, EDITIONS[key], (FIXTURES / f"{key}.txt").read_text(encoding="utf-8"), embedder=None
        )
    await seed_content(db, CONTENT_DIR)
    es = await db.scalar(
        select(SourcePassage).where(
            SourcePassage.language == "es", SourcePassage.chapter == 1, SourcePassage.paragraph_index == 1
        )
    )
    return es


def _good_draft(es_id: uuid.UUID) -> dict:
    return {
        "tl": "Isang hapunan ang naghintay sa akin sa Maynila.",
        "en": "A dinner awaited me in Manila.",
        "quoted_spans": [{"text": "daba una cena", "passage_id": str(es_id)}],
    }


def _bad_draft(es_id: uuid.UUID) -> dict:
    return {
        "tl": "Sabi ko noon.",
        "en": "I said then.",
        "quoted_spans": [{"text": "I never wrote this", "passage_id": str(es_id)}],
    }


@pytest.fixture
def fake_llm(client):
    from rizalai.main import app

    fake = FakeLLMClient()
    app.dependency_overrides[get_llm_client] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_llm_client, None)


async def _get(client, token, lesson=LESSON):
    return await client.get(f"/lessons/{lesson}/reflection", headers={"Authorization": f"Bearer {token}"})


async def test_requires_auth_and_known_lesson(client, db, fake_llm):
    await _prepare(db)
    assert (await client.get(f"/lessons/{LESSON}/reflection")).status_code == 401
    _, token = mint_token()
    assert (await _get(client, token, uuid.uuid4())).status_code == 404


async def test_generates_once_validates_and_caches(client, db, fake_llm):
    es = await _prepare(db)
    fake_llm.queue(_good_draft(es.id))
    _, token = mint_token()

    first = await _get(client, token)
    assert first.status_code == 200, first.text
    body = first.json()
    assert body["status"] == "published"
    assert body["reflection"]["tl"].startswith("Isang hapunan")
    assert body["reflection"]["quoted_spans"][0]["passage_id"] == str(es.id)
    assert [layer["language"] for layer in body["layers"]] == ["es", "tl", "en"]
    assert body["layers"][1]["label"].startswith("Tagalog")
    assert "1909" in body["layers"][1]["label"]
    assert body["prompt_version"] == "v1"
    assert fake_llm.calls == 1

    second = await _get(client, token)
    assert second.json() == body
    assert fake_llm.calls == 1


async def test_invalid_citation_regenerates_once_then_falls_back(client, db, fake_llm):
    es = await _prepare(db)
    fake_llm.queue(_bad_draft(es.id), _bad_draft(es.id))
    _, token = mint_token()
    response = await _get(client, token)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "fallback"
    assert body["reflection"] is None
    assert len(body["layers"]) == 3
    assert fake_llm.calls == 2
    row = await db.scalar(select(GeneratedContentCache))
    assert row is not None and row.status == "fallback" and row.citations_valid is False


async def test_second_attempt_can_succeed(client, db, fake_llm):
    es = await _prepare(db)
    fake_llm.queue(_bad_draft(es.id), _good_draft(es.id))
    _, token = mint_token()
    body = (await _get(client, token)).json()
    assert body["status"] == "published"
    assert fake_llm.calls == 2


async def test_rejected_row_regenerates(client, db, fake_llm):
    es = await _prepare(db)
    fake_llm.queue(_good_draft(es.id), _good_draft(es.id))
    _, token = mint_token()
    await _get(client, token)
    row = await db.scalar(select(GeneratedContentCache))
    await reject_reflection(db, row.id)
    await _get(client, token)
    assert fake_llm.calls == 2
    await db.refresh(row)
    assert row.status == "published"


async def test_prompt_receives_pinned_passages(client, db, fake_llm):
    es = await _prepare(db)
    fake_llm.queue(_good_draft(es.id))
    _, token = mint_token()
    await _get(client, token)
    assert str(es.id) in fake_llm.last_user_prompt
    assert es.text[:40] in fake_llm.last_user_prompt
