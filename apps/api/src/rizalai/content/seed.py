"""Seed units, lessons, and exercises from content YAML. Idempotent.

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

from rizalai.content.loader import content_hash, exercise_id, lesson_id, load_content, unit_id
from rizalai.contracts.lesson import LessonContent, PassageRef
from rizalai.db.models import Exercise, Lesson, SourcePassage, Unit

log = logging.getLogger(__name__)

ANSWER_FIELDS = frozenset({"answer_tokens", "correct_index"})


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


async def _seed_lesson(
    session: AsyncSession, unit_uuid: uuid.UUID, order_index: int, lesson: LessonContent, report: SeedReport
) -> None:
    lid = lesson_id(lesson.slug)
    passage_ids, unresolved = await resolve_passage_ids(session, lesson.source_passages)
    report.unresolved_passages += unresolved

    values = {
        "id": lid,
        "unit_id": unit_uuid,
        "slug": lesson.slug,
        "title": lesson.title,
        "order_index": order_index,
        "version": content_hash(lesson),
        "published": lesson.published,
        "estimated_minutes": lesson.estimated_minutes,
        "vignette": [b.model_dump(mode="json") for b in lesson.vignette],
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


async def seed_content(session: AsyncSession, content_dir: Path) -> SeedReport:
    report = SeedReport()
    for unit in load_content(content_dir):
        uid = unit_id(unit.slug)
        values = {
            "id": uid,
            "slug": unit.slug,
            "title": unit.title,
            "order_index": unit.order_index,
            "published": unit.published,
        }
        stmt = insert(Unit).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"], set_={k: v for k, v in values.items() if k != "id"}
        )
        await session.execute(stmt)
        report.units += 1
        for order, lesson in enumerate(unit.lessons):
            await _seed_lesson(session, uid, order, lesson, report)
    await session.commit()
    return report
