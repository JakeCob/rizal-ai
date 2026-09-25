"""Behaviors for `rizalai bootstrap` (plan 007, D37), against rizalai_test
with the small Gutenberg fixtures and the fixture content:
- Given a migrated empty database, when bootstrap runs, then it ingests the
  three editions, seeds, reports counts equal to the content's own totals,
  and succeeds; a second run skips every edition and changes no lesson.
- Given a missing corpus file or a digest mismatch in any edition, then it
  fails before writing anything.
- Given content whose refs cannot resolve against the corpus, then it fails
  before seeding writes anything.
- Given a database behind the code's migration head, then it fails before
  touching anything, and says to run alembic upgrade head.
- Given content that drops a lesson or exercise learners have rows for, then
  it refuses and leaves the rows in place, unless learner data loss is
  explicitly allowed; deletions with no learner rows are listed and done.
- Given a unit removed from content, then its row goes too (same guard).
- Given --dry-run, then it prints the plan and writes nothing.
- Given an edition already present, when --embed is passed, then it still
  embeds the missing vectors.
- Given audio URLs in the database, when bootstrap seeds without an engine,
  then vignette and listen_tap URLs are kept; render-audio overwrites them;
  a changed line drops its URL.
- Given the database counts disagree with the content after seeding, then
  it fails.
- Given another run holding the advisory lock, then bootstrap waits for it.
"""

import asyncio
import hashlib
import shutil
import time
import uuid
from pathlib import Path

import pytest
import yaml
from sqlalchemy import func, select, text

from rizalai.audio.engines import FakeTTS
from rizalai.audio.render import render_lines
from rizalai.audio.store import LocalAudioStore
from rizalai.content.loader import exercise_id, lesson_id, load_content, unit_id
from rizalai.content.seed import SeedReport, seed_content
from rizalai.corpus.embeddings import FakeEmbedder
from rizalai.db.models import Exercise, ExerciseAttempt, Lesson, SourcePassage, Unit, User, UserProgress
from rizalai.ops import bootstrap as ops
from rizalai.ops.bootstrap import advisory_lock, bootstrap, database_revision, script_head

pytestmark = pytest.mark.anyio

API_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = API_ROOT / "tests" / "fixtures"
CONTENT_DIR = FIXTURES / "content"
SOURCES = {key: FIXTURES / "gutenberg" / f"{key}.txt" for key in ("noli_es", "noli_tl", "noli_en")}
DIGESTS = {key: hashlib.sha256(path.read_bytes()).hexdigest() for key, path in SOURCES.items()}
HEAD = script_head(API_ROOT / "alembic.ini")
SCAFFOLD = lesson_id("scaffold-placeholder")


async def _run(db, content_dir: Path = CONTENT_DIR, **kwargs):
    kwargs.setdefault("sources", SOURCES)
    return await bootstrap(db, content_dir=content_dir, script_head=HEAD, **kwargs)


async def _count(db, model) -> int:
    return int(await db.scalar(select(func.count()).select_from(model)) or 0)


def _copy_content(tmp_path: Path) -> Path:
    work = tmp_path / "content"
    shutil.copytree(CONTENT_DIR, work)
    return work


def _drop_lesson(work: Path, filename: str) -> None:
    unit_file = work / "units" / "01-test-unit" / "unit.yaml"
    unit = yaml.safe_load(unit_file.read_text(encoding="utf-8"))
    unit["lessons"].remove(filename)
    unit_file.write_text(yaml.safe_dump(unit), encoding="utf-8")


async def _learner_on_scaffold(db) -> uuid.UUID:
    uid = uuid.uuid4()
    db.add(User(id=uid))
    await db.flush()
    db.add(UserProgress(user_id=uid, lesson_id=SCAFFOLD, lesson_version="v", completed_at=None))
    db.add(
        ExerciseAttempt(
            user_id=uid,
            exercise_id=exercise_id("scaffold-placeholder", "ex1"),
            lesson_id=SCAFFOLD,
            correct=True,
            response={"tokens": ["x"]},
            duration_ms=1,
        )
    )
    await db.commit()
    return uid


async def test_bootstrap_ingests_seeds_and_is_idempotent(db):
    first = await _run(db, digests=DIGESTS)
    assert first.ok, first.problems
    assert [e.skipped for e in first.editions] == [False, False, False]
    assert (first.counts.units, first.counts.lessons, first.counts.exercises) == (1, 4, 6)
    assert first.lessons_changed == 4
    passages = await _count(db, SourcePassage)
    assert passages == sum(e.parsed for e in first.editions)

    second = await _run(db, digests=DIGESTS)
    assert second.ok, second.problems
    assert [e.skipped for e in second.editions] == [True, True, True]
    assert second.lessons_changed == 0
    assert await _count(db, SourcePassage) == passages
    assert "skip" in second.summary()


async def test_a_missing_corpus_file_fails_before_any_write(db, tmp_path):
    sources = {**SOURCES, "noli_en": tmp_path / "missing.txt"}
    result = await _run(db, sources=sources)
    assert not result.ok and "missing corpus file" in result.problems[0]
    assert await _count(db, SourcePassage) == 0


async def test_a_digest_mismatch_fails_before_any_write(db):
    result = await _run(db, digests={**DIGESTS, "noli_tl": "0" * 64})
    assert not result.ok and "sha256" in result.problems[0]
    assert await _count(db, SourcePassage) == 0  # noli_es was not ingested either


async def test_unresolved_refs_fail_before_seeding(db, tmp_path):
    work = _copy_content(tmp_path)
    lesson_file = work / "units" / "01-test-unit" / "01-scaffold-placeholder.yaml"
    lesson = yaml.safe_load(lesson_file.read_text(encoding="utf-8"))
    lesson["source_passages"][0]["paragraph_index"] = 999
    lesson_file.write_text(yaml.safe_dump(lesson, allow_unicode=True), encoding="utf-8")

    result = await _run(db, content_dir=work)
    assert not result.ok
    assert any("unresolved" in p for p in result.problems)
    assert await _count(db, Lesson) == 0
    assert await _count(db, SourcePassage) == 0


async def test_a_database_behind_the_head_fails_before_any_work(db):
    result = await bootstrap(db, content_dir=CONTENT_DIR, sources=SOURCES, script_head="not-a-revision")
    assert not result.ok
    assert "alembic upgrade head" in result.problems[0]
    assert await _count(db, SourcePassage) == 0
    assert await database_revision(db) == HEAD


async def test_dropping_a_lesson_with_learner_rows_is_refused(db, tmp_path):
    await _run(db)
    await _learner_on_scaffold(db)
    work = _copy_content(tmp_path)
    _drop_lesson(work, "01-scaffold-placeholder.yaml")

    refused = await _run(db, content_dir=work)
    assert not refused.ok
    message = " ".join(refused.problems)
    assert "scaffold-placeholder" in message and "allow-learner-data-loss" in message
    assert refused.deletions.learner_rows == {"user_progress": 1, "exercise_attempts": 1, "review_queue": 0}
    assert await db.get(Lesson, SCAFFOLD) is not None
    assert await _count(db, UserProgress) == 1

    allowed = await _run(db, content_dir=work, allow_learner_data_loss=True)
    assert allowed.ok, allowed.problems
    assert await db.get(Lesson, SCAFFOLD) is None
    assert await _count(db, UserProgress) == 0


async def test_deletions_without_learner_rows_are_listed_and_done(db, tmp_path):
    await _run(db)
    work = _copy_content(tmp_path)
    _drop_lesson(work, "02-placeholder.yaml")
    result = await _run(db, content_dir=work)
    assert result.ok, result.problems
    assert result.deletions.lessons == ["noli-ch02-placeholder"]
    assert "delete lesson noli-ch02-placeholder" in result.summary()
    assert await db.get(Lesson, lesson_id("noli-ch02-placeholder")) is None


async def test_a_removed_unit_is_deleted(db, tmp_path):
    work = _copy_content(tmp_path)
    extra = work / "units" / "02-extra"
    extra.mkdir()
    (extra / "unit.yaml").write_text(
        'slug: extra-unit\ntitle: "Extra"\norder_index: 2\nlessons:\n  - 01-stub.yaml\n', encoding="utf-8"
    )
    (extra / "01-stub.yaml").write_text(
        'slug: extra-stub\ntitle: "Stub"\npublished: false\n', encoding="utf-8"
    )
    assert (await _run(db, content_dir=work)).ok
    assert await db.get(Unit, unit_id("extra-unit")) is not None

    shutil.rmtree(extra)
    result = await _run(db, content_dir=work)
    assert result.ok, result.problems
    assert result.deletions.units == ["extra-unit"]
    assert await db.get(Unit, unit_id("extra-unit")) is None
    assert result.counts.units == 1


async def test_dry_run_prints_the_plan_and_writes_nothing(db, tmp_path):
    empty = await _run(db, dry_run=True)
    assert empty.ok and empty.dry_run
    assert [e.skipped for e in empty.editions] == [False, False, False]
    assert "would ingest" in empty.summary()
    assert await _count(db, SourcePassage) == 0 and await _count(db, Lesson) == 0

    await _run(db)
    await _learner_on_scaffold(db)
    work = _copy_content(tmp_path)
    _drop_lesson(work, "01-scaffold-placeholder.yaml")
    plan = await _run(db, content_dir=work, dry_run=True)
    assert plan.deletions.lessons == ["scaffold-placeholder"]
    assert "dry run" in plan.summary()
    assert await db.get(Lesson, SCAFFOLD) is not None


async def test_embed_runs_on_an_edition_already_present(db):
    await _run(db)
    result = await _run(db, embedder=FakeEmbedder())
    assert result.ok, result.problems
    assert [e.skipped for e in result.editions] == [True, True, True]
    assert all(e.embedded == e.parsed for e in result.editions)
    missing = await db.scalar(
        select(func.count()).select_from(SourcePassage).where(SourcePassage.embedding.is_(None))
    )
    assert missing == 0


async def test_audio_urls_are_kept_overwritten_and_dropped(db, tmp_path):
    await _run(db)
    lesson = await db.get(Lesson, SCAFFOLD)
    assert lesson is not None
    vignette = [dict(b) for b in lesson.vignette]
    vignette[0]["audio_url"] = "https://cdn.test/audio/b1.mp3"
    lesson.vignette = vignette
    listen = await db.get(Exercise, exercise_id("scaffold-placeholder", "ex3"))
    assert listen is not None
    listen.payload = {**listen.payload, "audio_url": "https://cdn.test/audio/ex3.mp3"}
    await db.commit()

    kept = await _run(db)
    assert kept.ok, kept.problems
    await db.refresh(lesson)
    await db.refresh(listen)
    assert lesson.vignette[0]["audio_url"] == "https://cdn.test/audio/b1.mp3"
    assert listen.payload["audio_url"] == "https://cdn.test/audio/ex3.mp3"

    store = LocalAudioStore(tmp_path / "audio", base_url="https://cdn.render/audio")
    engine = FakeTTS()
    placeholder = load_content(CONTENT_DIR)[0].lessons[0]
    render_lines([placeholder.vignette[0].tl], engine, store)
    await seed_content(db, CONTENT_DIR, audio=(store, engine))  # what render-audio does
    await db.refresh(lesson)
    assert lesson.vignette[0]["audio_url"].startswith("https://cdn.render/audio/")

    work = _copy_content(tmp_path)
    lesson_file = work / "units" / "01-test-unit" / "01-scaffold-placeholder.yaml"
    data = yaml.safe_load(lesson_file.read_text(encoding="utf-8"))
    data["vignette"][0]["tl"] = "Nagkaroon ng hapunan sa bahay ni Kapitan Tiago."
    lesson_file.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    changed = await _run(db, content_dir=work)
    assert changed.ok, changed.problems
    await db.refresh(lesson)
    assert lesson.vignette[0]["audio_url"] is None  # the old file speaks the old line


async def test_a_count_mismatch_fails(db, monkeypatch):
    async def seed_nothing(session, content_dir, audio=None, **kwargs):
        return SeedReport()

    monkeypatch.setattr(ops, "seed_content", seed_nothing)
    result = await _run(db)
    assert not result.ok
    assert any("differ from the content" in p for p in result.problems)


async def test_bootstrap_waits_on_the_advisory_lock(db, engine):
    async with engine.connect() as holder, engine.connect() as waiter:
        async with advisory_lock(holder):
            started = time.monotonic()
            task = asyncio.create_task(_run(db, lock_conn=waiter))
            await asyncio.sleep(0.5)
            assert not task.done()
        result = await task
        assert result.ok, result.problems
        assert time.monotonic() - started >= 0.5
        assert await holder.scalar(text("select pg_try_advisory_lock(7007)")) is True
        await holder.execute(text("select pg_advisory_unlock(7007)"))
