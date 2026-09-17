"""Behaviors:
- Given parsed passages, when ingested, then rows exist per locator with
  translator and license_note, and a second run inserts nothing new.
- Given rows, when embedded with the fake embedder, then dense, sparse,
  and embedding_model are filled.
- Given ingested passages, when content is seeded, then the placeholder
  lesson's source passage refs resolve to ids.
"""

from pathlib import Path

import pytest
from sqlalchemy import func, select

from rizalai.content.loader import lesson_id
from rizalai.content.seed import seed_content
from rizalai.corpus.embeddings import FakeEmbedder
from rizalai.corpus.gutenberg import EDITIONS
from rizalai.corpus.ingest import ingest_text
from rizalai.db.models import Lesson, SourcePassage

pytestmark = pytest.mark.anyio

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "gutenberg"
CONTENT_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "content"
REAL_CONTENT_DIR = Path(__file__).resolve().parents[3].parent / "content"


async def _count(db, **where) -> int:
    stmt = select(func.count()).select_from(SourcePassage)
    for k, v in where.items():
        stmt = stmt.where(getattr(SourcePassage, k) == v)
    return await db.scalar(stmt)


async def test_ingest_is_idempotent_and_records_provenance(db):
    raw = (FIXTURES / "noli_tl.txt").read_text(encoding="utf-8")
    report = await ingest_text(db, EDITIONS["noli_tl"], raw, embedder=None)
    assert report.inserted == 6
    assert await _count(db, work="noli", language="tl") == 6

    again = await ingest_text(db, EDITIONS["noli_tl"], raw, embedder=None)
    assert again.inserted == 0
    assert again.updated == 6
    assert await _count(db, work="noli", language="tl") == 6

    row = await db.scalar(
        select(SourcePassage).where(
            SourcePassage.work == "noli",
            SourcePassage.language == "tl",
            SourcePassage.chapter == 1,
            SourcePassage.paragraph_index == 1,
        )
    )
    assert row is not None
    assert row.translator == "poblete_1909"
    assert "gutenberg.org/ebooks/20228" in row.license_note
    assert row.text.startswith("Nag-anyaya")
    assert row.embedding is None


async def test_embed_step_fills_vectors(db):
    raw = (FIXTURES / "noli_en.txt").read_text(encoding="utf-8")
    report = await ingest_text(db, EDITIONS["noli_en"], raw, embedder=FakeEmbedder(), batch_size=4)
    assert report.embedded == 6
    rows = (await db.scalars(select(SourcePassage).where(SourcePassage.language == "en"))).all()
    assert all(r.embedding is not None and len(r.embedding) == 1024 for r in rows)
    assert all(r.sparse and r.embedding_model == "fake" for r in rows)


async def test_seed_resolves_passage_refs_after_ingest(db):
    for key in ("noli_es", "noli_tl"):
        await ingest_text(
            db, EDITIONS[key], (FIXTURES / f"{key}.txt").read_text(encoding="utf-8"), embedder=None
        )
    report = await seed_content(db, CONTENT_DIR)
    assert report.unresolved_passages == 0
    lesson = await db.get(Lesson, lesson_id("scaffold-placeholder"))
    assert lesson is not None
    assert len(lesson.source_passage_ids) == 2


async def test_seed_aligns_grouped_passage_refs(db):
    """Refs that share a group within a lesson get the same passage_group_id,
    derived from the lesson slug and group name, so alignment is recorded
    by content and never by chapter number (docs/tech-debt.md item 10)."""
    from rizalai.content.seed import align_passage_groups
    from rizalai.contracts.lesson import PassageRef

    for key in ("noli_es", "noli_tl"):
        await ingest_text(
            db, EDITIONS[key], (FIXTURES / f"{key}.txt").read_text(encoding="utf-8"), embedder=None
        )
    refs = [
        PassageRef(work="noli", language="es", chapter=1, paragraph_index=1, group="opening"),
        PassageRef(work="noli", language="tl", chapter=1, paragraph_index=1, group="opening"),
        PassageRef(work="noli", language="es", chapter=1, paragraph_index=2),
    ]
    grouped = await align_passage_groups(db, "some-lesson", refs)
    assert grouped == 2
    rows = (
        await db.scalars(
            select(SourcePassage).where(SourcePassage.chapter == 1, SourcePassage.paragraph_index == 1)
        )
    ).all()
    ids = {r.passage_group_id for r in rows}
    assert len(ids) == 1 and None not in ids
    ungrouped = await db.scalar(
        select(SourcePassage.passage_group_id).where(
            SourcePassage.language == "es", SourcePassage.chapter == 1, SourcePassage.paragraph_index == 2
        )
    )
    assert ungrouped is None
