"""`rizalai bootstrap`: bring a migrated database to the content (D37).

One idempotent run, safe to repeat and safe to start twice. It plans first,
read-only, and writes only when the whole plan is sound:
1. take a Postgres advisory lock, so a second run waits instead of racing;
2. check the database is at the code's migration head;
3. read every edition's committed text and check its digest;
4. check every passage ref in the content resolves against those texts;
5. work out what seeding would delete (lessons and exercises the content no
   longer has, units no longer in content) and count the learner rows
   (user_progress, exercise_attempts, review_queue) that would cascade with
   them; refuse if there are any, unless learner data loss is allowed;
then, unless it is a dry run: ingest each edition (skipping an edition whose
row count already matches, still embedding when asked), seed without
committing, refuse and roll back if a ref failed to resolve, commit, and
check the database's units, lessons and exercises equal the content's own
totals. Any problem makes the run fail, so a deploy script can stop on it.
"""

import hashlib
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager, nullcontext
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession

from rizalai.content.loader import UnitContent, content_hash, exercise_id, lesson_id, load_content, unit_id
from rizalai.content.seed import SeedReport, seed_content
from rizalai.corpus.embeddings import Embedder
from rizalai.corpus.gutenberg import EDITIONS, parse_edition
from rizalai.corpus.ingest import edition_row_count, ingest_text
from rizalai.db.models import Exercise, ExerciseAttempt, Lesson, ReviewQueue, Unit, UserProgress

LOCK_KEY = 7007  # plan 007

Locator = tuple[str, str, int, int]


@asynccontextmanager
async def advisory_lock(conn: AsyncConnection) -> AsyncIterator[None]:
    """Hold a session-level advisory lock on `conn` for the block. The lock
    belongs to the connection, so it is taken on one kept open for the run."""
    await conn.execute(text("select pg_advisory_lock(:key)"), {"key": LOCK_KEY})
    await conn.commit()
    try:
        yield
    finally:
        await conn.execute(text("select pg_advisory_unlock(:key)"), {"key": LOCK_KEY})
        await conn.commit()


def script_head(alembic_ini: Path) -> str:
    """The newest migration in the code."""
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    head = ScriptDirectory.from_config(Config(str(alembic_ini))).get_current_head()
    if head is None:
        raise RuntimeError(f"no migrations found from {alembic_ini}")
    return head


async def database_revision(session: AsyncSession) -> str | None:
    if await session.scalar(text("select to_regclass('alembic_version')")) is None:
        return None
    revision = await session.scalar(text("select version_num from alembic_version"))
    return str(revision) if revision is not None else None


@dataclass
class EditionOutcome:
    key: str
    parsed: int = 0
    inserted: int = 0
    updated: int = 0
    embedded: int = 0
    skipped: bool = False


@dataclass
class Counts:
    units: int = 0
    lessons: int = 0
    exercises: int = 0


@dataclass
class Deletions:
    """What seeding would delete, and the learner rows that would go with it."""

    units: list[str] = field(default_factory=list)
    lessons: list[str] = field(default_factory=list)
    exercises: list[str] = field(default_factory=list)
    learner_rows: dict[str, int] = field(default_factory=dict)

    @property
    def any(self) -> bool:
        return bool(self.units or self.lessons or self.exercises)

    @property
    def learner_total(self) -> int:
        return sum(self.learner_rows.values())


@dataclass
class BootstrapReport:
    revision: str | None = None
    dry_run: bool = False
    editions: list[EditionOutcome] = field(default_factory=list)
    deletions: Deletions = field(default_factory=Deletions)
    unresolved_refs: list[str] = field(default_factory=list)
    seed: SeedReport = field(default_factory=SeedReport)
    lessons_changed: int = 0
    expected: Counts = field(default_factory=Counts)
    counts: Counts = field(default_factory=Counts)
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems

    def summary(self) -> str:
        lines = [f"database revision: {self.revision or 'none'}"]
        if self.dry_run:
            lines.append("dry run: nothing written")
        for e in self.editions:
            if e.skipped:
                line = f"{e.key}: skip, {e.parsed} passages already present"
            elif self.dry_run:
                line = f"{e.key}: would ingest {e.parsed} passages"
            else:
                line = f"{e.key}: parsed {e.parsed}, inserted {e.inserted}, updated {e.updated}"
            lines.append(line + (f", embedded {e.embedded}" if e.embedded else ""))
        d = self.deletions
        verb = "would delete" if self.dry_run else "delete"
        lines += [f"{verb} unit {slug}" for slug in d.units]
        lines += [f"{verb} lesson {slug}" for slug in d.lessons]
        lines += [f"{verb} exercise {key}" for key in d.exercises]
        if d.any:
            rows = ", ".join(f"{name} {n}" for name, n in d.learner_rows.items())
            lines.append(f"learner rows that would cascade: {rows}")
        if self.expected.lessons:
            x = self.expected
            if self.dry_run:
                lines.append(
                    f"content: {x.units} units, {x.lessons} lessons, {x.exercises} exercises; "
                    f"{self.lessons_changed} lessons new or changed"
                )
            elif self.editions and not self.problems or self.counts.lessons:
                lines.append(
                    f"seed: {self.lessons_changed} lessons new or changed; "
                    f"{self.seed.unresolved_passages} passage refs unresolved"
                )
                c = self.counts
                lines.append(
                    f"counts: {c.units} units, {c.lessons} lessons, {c.exercises} exercises "
                    f"(content: {x.units}, {x.lessons}, {x.exercises})"
                )
        lines += [f"problem: {p}" for p in self.problems]
        lines.append("bootstrap ok" if self.ok else "bootstrap FAILED")
        return "\n".join(lines)


async def _count(session: AsyncSession, model: Any, *where: Any) -> int:
    return int(await session.scalar(select(func.count()).select_from(model).where(*where)) or 0)


def _content_locators(units: list[UnitContent]) -> dict[Locator, str]:
    refs: dict[Locator, str] = {}
    for unit in units:
        for lesson in unit.lessons:
            for ref in lesson.source_passages:
                refs[(ref.work, ref.language, ref.chapter, ref.paragraph_index)] = lesson.slug
    return refs


async def _plan_deletions(session: AsyncSession, units: list[UnitContent]) -> Deletions:
    keep_units = {unit_id(u.slug) for u in units}
    keep_lessons = {lesson_id(lesson.slug) for u in units for lesson in u.lessons}
    keep_exercises = {
        exercise_id(lesson.slug, e.key) for u in units for lesson in u.lessons for e in lesson.exercises
    }
    deletions = Deletions()
    for unit_row in await session.execute(select(Unit.id, Unit.slug).order_by(Unit.order_index)):
        if unit_row.id not in keep_units:
            deletions.units.append(unit_row.slug)
    doomed_lessons = []
    for lesson_row in await session.execute(select(Lesson.id, Lesson.slug).order_by(Lesson.slug)):
        if lesson_row.id not in keep_lessons:
            deletions.lessons.append(lesson_row.slug)
            doomed_lessons.append(lesson_row.id)
    doomed_exercises = []
    stmt = select(Exercise.id, Exercise.lesson_id, Lesson.slug, Exercise.payload).join(
        Lesson, Lesson.id == Exercise.lesson_id
    )
    for row in await session.execute(stmt.order_by(Lesson.slug, Exercise.order_index)):
        if row.lesson_id in doomed_lessons:
            doomed_exercises.append(row.id)
        elif row.id not in keep_exercises:
            deletions.exercises.append(f"{row.slug}:{row.payload.get('key')}")
            doomed_exercises.append(row.id)
    deletions.learner_rows = {
        "user_progress": await _count(session, UserProgress, UserProgress.lesson_id.in_(doomed_lessons)),
        "exercise_attempts": await _count(
            session,
            ExerciseAttempt,
            or_(
                ExerciseAttempt.lesson_id.in_(doomed_lessons),
                ExerciseAttempt.exercise_id.in_(doomed_exercises),
            ),
        ),
        "review_queue": await _count(session, ReviewQueue, ReviewQueue.exercise_id.in_(doomed_exercises)),
    }
    return deletions


async def bootstrap(
    session: AsyncSession,
    *,
    content_dir: Path,
    sources: Mapping[str, Path],
    script_head: str,
    digests: Mapping[str, str] | None = None,
    embedder: Embedder | None = None,
    lock_conn: AsyncConnection | None = None,
    dry_run: bool = False,
    allow_learner_data_loss: bool = False,
) -> BootstrapReport:
    lock = advisory_lock(lock_conn) if lock_conn is not None else nullcontext()
    async with lock:
        report = BootstrapReport(dry_run=dry_run)
        await _run(
            report, session, content_dir, sources, script_head, digests, embedder, allow_learner_data_loss
        )
        return report


async def _run(
    report: BootstrapReport,
    session: AsyncSession,
    content_dir: Path,
    sources: Mapping[str, Path],
    head: str,
    digests: Mapping[str, str] | None,
    embedder: Embedder | None,
    allow_learner_data_loss: bool,
) -> None:
    report.revision = await database_revision(session)
    if report.revision != head:
        report.problems.append(
            f"database is at {report.revision or 'no revision'} but the code expects {head}: "
            "run alembic upgrade head first"
        )
        return

    units = load_content(content_dir)
    report.expected = Counts(
        units=len(units),
        lessons=sum(len(u.lessons) for u in units),
        exercises=sum(len(lesson.exercises) for u in units for lesson in u.lessons),
    )

    # Every file and digest, before any write.
    texts: dict[str, str] = {}
    for key, path in sources.items():
        if not path.is_file():
            report.problems.append(f"{key}: missing corpus file {path}")
            continue
        data = path.read_bytes()
        if digests is not None and hashlib.sha256(data).hexdigest() != digests[key]:
            report.problems.append(f"{key}: {path} does not match its pinned sha256")
            continue
        texts[key] = data.decode("utf-8", errors="replace")
    if report.problems:
        return

    # Every ref against the texts the database will hold, before any write.
    parsed = {key: parse_edition(EDITIONS[key], raw) for key, raw in texts.items()}
    available = {(p.work, p.language, p.chapter, p.paragraph_index) for ps in parsed.values() for p in ps}
    for locator, slug in _content_locators(units).items():
        if locator not in available:
            report.unresolved_refs.append(f"{slug} {locator[1]} {locator[2]}:{locator[3]}")
    if report.unresolved_refs:
        report.problems.append(
            f"{len(report.unresolved_refs)} passage refs unresolved: " + ", ".join(report.unresolved_refs[:5])
        )
        return

    # What seeding would delete, and whose data would go with it.
    report.deletions = await _plan_deletions(session, units)
    if report.deletions.learner_total and not allow_learner_data_loss:
        d = report.deletions
        doomed = ", ".join([*(f"unit {u}" for u in d.units), *d.lessons, *d.exercises])
        rows = ", ".join(f"{name} {n}" for name, n in d.learner_rows.items() if n)
        report.problems.append(
            f"seeding would delete {doomed}, taking learner rows with it ({rows}); "
            "change the content, or pass --allow-learner-data-loss"
        )
        return

    before = dict((await session.execute(select(Lesson.id, Lesson.version))).tuples().all())
    report.lessons_changed = sum(
        1
        for unit in units
        for lesson in unit.lessons
        if before.get(lesson_id(lesson.slug)) != content_hash(lesson)
    )
    for key in texts:
        spec = EDITIONS[key]
        present = await edition_row_count(session, spec)
        report.editions.append(
            EditionOutcome(key, parsed=len(parsed[key]), skipped=present == len(parsed[key]))
        )
    if report.dry_run:
        return

    for outcome in report.editions:
        result = await ingest_text(
            session, EDITIONS[outcome.key], texts[outcome.key], embedder, skip_if_present=True
        )
        outcome.inserted, outcome.updated, outcome.embedded = result.inserted, result.updated, result.embedded
        outcome.skipped = result.skipped

    report.seed = await seed_content(session, content_dir, prune_units=True, commit=False)
    if report.seed.unresolved_passages:
        await session.rollback()
        report.problems.append(
            f"{report.seed.unresolved_passages} passage refs unresolved; the seed was rolled back"
        )
        return
    await session.commit()
    report.counts = Counts(
        units=await _count(session, Unit),
        lessons=await _count(session, Lesson),
        exercises=await _count(session, Exercise),
    )
    if report.counts != report.expected:
        report.problems.append(
            f"database counts {report.counts} differ from the content's own totals {report.expected}"
        )
