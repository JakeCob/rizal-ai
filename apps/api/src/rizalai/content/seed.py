"""Seed units, lessons, and exercises from content YAML. Idempotent.

Lessons dropped from a unit.yaml and exercises whose key vanished are
deleted, and with prune_units so are units no longer in content; learner
rows referencing them cascade. `rizalai bootstrap` guards that. A null
audio_url in YAML keeps the URL already in the database for an unchanged
line (so a plain seed keeps what render-audio set), which also means a
hand-set URL cannot be cleared by removing it from YAML alone.

Exercises are stored as payload (what the learner sees) and answer (the key)
in separate columns. The API merges them for the client today (DECISIONS.md
D15); the split keeps server-only grading possible later.
"""

import logging
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from rizalai.audio.engines import TTSEngine
from rizalai.audio.render import key_for
from rizalai.audio.store import AudioStore
from rizalai.content.loader import NAMESPACE, content_hash, exercise_id, lesson_id, load_content, unit_id
from rizalai.contracts.lesson import LessonContent, PassageRef
from rizalai.db.models import Exercise, Lesson, SourcePassage, Unit

log = logging.getLogger(__name__)

ANSWER_FIELDS = frozenset({"answer_tokens", "accepted_orders", "correct_index"})


@dataclass
class SeedReport:
    units: int = 0
    lessons: int = 0
    exercises: int = 0
    unresolved_passages: int = 0


def split_exercise(exercise_dump: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = {k: v for k, v in exercise_dump.items() if k not in ANSWER_FIELDS}
    answer = {k: v for k, v in exercise_dump.items() if k in ANSWER_FIELDS}
    return payload, answer


async def resolve_passage_ids(session: AsyncSession, refs: list[PassageRef]) -> tuple[list[uuid.UUID], int]:
    ids: list[uuid.UUID] = []
    unresolved = 0
    for ref in refs:
        stmt = select(SourcePassage.id).where(
            SourcePassage.work == ref.work,
            SourcePassage.language == ref.language,
            SourcePassage.chapter == ref.chapter,
            SourcePassage.paragraph_index == ref.paragraph_index,
        )
        found = await session.scalar(stmt)
        if found is None:
            unresolved += 1
            log.warning("source passage not ingested yet: %s", ref.model_dump())
        else:
            ids.append(found)
    return ids, unresolved


def _locator_clause(ref: PassageRef) -> list[Any]:
    return [
        SourcePassage.work == ref.work,
        SourcePassage.language == ref.language,
        SourcePassage.chapter == ref.chapter,
        SourcePassage.paragraph_index == ref.paragraph_index,
    ]


async def align_passage_groups(session: AsyncSession, lesson_slug: str, refs: list[PassageRef]) -> int:
    """Stamp passage_group_id on refs that share a group. The id derives from
    the lesson slug and group name, so re-seeding is stable. Returns the
    number of rows updated. Alignment is by content, recorded by the author,
    never inferred from chapter numbers."""
    updated = 0
    for ref in refs:
        if ref.group is None:
            continue
        group_id = uuid.uuid5(NAMESPACE, f"group:{lesson_slug}:{ref.group}")
        result: Any = await session.execute(
            update(SourcePassage).where(*_locator_clause(ref)).values(passage_group_id=group_id)
        )
        updated += int(result.rowcount or 0)
    return updated


AudioSource = tuple[AudioStore, TTSEngine]


def _audio_url(audio: AudioSource | None, text: str) -> str | None:
    """URL of the pre-rendered file for this line, if the store has it (D12)."""
    if audio is None:
        return None
    store, engine = audio
    key = key_for(engine, text)
    return store.url(key) if store.exists(key) else None


def _url(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _kept(existing: dict[str, tuple[str, str | None]], line_id: str, text: str) -> str | None:
    """The URL a line already has in the database, if its text is unchanged.
    A plain seed (no audio source) keeps what render-audio set (D37); a
    changed line loses its URL because the old file speaks the old text."""
    found = existing.get(line_id)
    return found[1] if found and found[0] == text else None


async def _seed_lesson(
    session: AsyncSession,
    unit_uuid: uuid.UUID,
    order_index: int,
    lesson: LessonContent,
    report: SeedReport,
    audio: AudioSource | None = None,
) -> None:
    lid = lesson_id(lesson.slug)
    beats_before: dict[str, tuple[str, str | None]] = {}
    listen_before: dict[str, tuple[str, str | None]] = {}
    if audio is None:
        old = await session.get(Lesson, lid)
        if old is not None:
            beats_before = {str(b["line_id"]): (str(b["tl"]), _url(b.get("audio_url"))) for b in old.vignette}
        for row in await session.scalars(select(Exercise).where(Exercise.lesson_id == lid)):
            if row.type == "listen_tap":
                listen_before[str(row.payload.get("key"))] = (
                    str(row.payload.get("transcript_tl")),
                    _url(row.payload.get("audio_url")),
                )
    passage_ids, unresolved = await resolve_passage_ids(session, lesson.source_passages)
    report.unresolved_passages += unresolved
    await align_passage_groups(session, lesson.slug, lesson.source_passages)

    values = {
        "id": lid,
        "unit_id": unit_uuid,
        "slug": lesson.slug,
        "title": lesson.title,
        "order_index": order_index,
        "version": content_hash(lesson),
        "published": lesson.published,
        "estimated_minutes": lesson.estimated_minutes,
        "vignette": [
            {
                **b.model_dump(mode="json"),
                "audio_url": b.audio_url or _audio_url(audio, b.tl) or _kept(beats_before, b.line_id, b.tl),
            }
            for b in lesson.vignette
        ],
        "grammar_focus": lesson.grammar_focus,
        "target_vocab": [v.model_dump(mode="json") for v in lesson.target_vocab],
        "source_passage_ids": passage_ids,
    }
    stmt = insert(Lesson).values(**values)
    stmt = stmt.on_conflict_do_update(
        index_elements=["id"], set_={k: v for k, v in values.items() if k != "id"}
    )
    await session.execute(stmt)
    report.lessons += 1

    current_ids = [exercise_id(lesson.slug, e.key) for e in lesson.exercises]
    await session.execute(delete(Exercise).where(Exercise.lesson_id == lid, Exercise.id.not_in(current_ids)))
    # Park existing order indexes so reordering cannot collide on the unique constraint.
    await session.execute(
        update(Exercise).where(Exercise.lesson_id == lid).values(order_index=-Exercise.order_index - 1)
    )
    for order, exercise in enumerate(lesson.exercises):
        payload, answer = split_exercise(exercise.model_dump(mode="json"))
        if exercise.type == "listen_tap" and not payload.get("audio_url"):
            payload["audio_url"] = _audio_url(audio, exercise.transcript_tl) or _kept(
                listen_before, exercise.key, exercise.transcript_tl
            )
        ex_values = {
            "id": exercise_id(lesson.slug, exercise.key),
            "lesson_id": lid,
            "order_index": order,
            "type": exercise.type,
            "payload": payload,
            "answer": answer,
            "xp": exercise.xp,
        }
        ex_stmt = insert(Exercise).values(**ex_values)
        ex_stmt = ex_stmt.on_conflict_do_update(
            index_elements=["id"], set_={k: v for k, v in ex_values.items() if k != "id"}
        )
        await session.execute(ex_stmt)
        report.exercises += 1


async def seed_content(
    session: AsyncSession,
    content_dir: Path,
    audio: AudioSource | None = None,
    *,
    prune_units: bool = False,
    commit: bool = True,
) -> SeedReport:
    report = SeedReport()
    units = load_content(content_dir)
    if prune_units:
        await session.execute(delete(Unit).where(Unit.id.not_in([unit_id(u.slug) for u in units])))
    for unit in units:
        uid = unit_id(unit.slug)
        values = {
            "id": uid,
            "slug": unit.slug,
            "title": unit.title,
            "order_index": unit.order_index,
        }
        stmt = insert(Unit).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"], set_={k: v for k, v in values.items() if k != "id"}
        )
        await session.execute(stmt)
        report.units += 1
        # Lessons dropped from unit.yaml leave the spine. Park the order of
        # the survivors so reordering cannot collide on (unit_id, order_index).
        keep = [lesson_id(lesson.slug) for lesson in unit.lessons]
        await session.execute(delete(Lesson).where(Lesson.unit_id == uid, Lesson.id.not_in(keep)))
        await session.execute(
            update(Lesson).where(Lesson.unit_id == uid).values(order_index=-Lesson.order_index - 1)
        )
        for order, lesson in enumerate(unit.lessons):
            await _seed_lesson(session, uid, order, lesson, report, audio)
    if commit:
        await session.commit()
    return report
