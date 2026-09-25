"""Lesson lookups and shaping shared by the routers, so routers never import
from each other. Unpublished lessons, and exercises that belong to them, are
404, the same as an unknown id, so a direct link or a stale review row cannot
load, grade, or complete them."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rizalai.contracts.lesson import ExerciseAdapter, ExerciseOut
from rizalai.db.models import Exercise, Lesson


async def get_published_lesson(session: AsyncSession, lesson_id: uuid.UUID) -> Lesson:
    lesson = await session.get(Lesson, lesson_id)
    if lesson is None or not lesson.published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="lesson not found")
    return lesson


async def get_published_exercise(session: AsyncSession, exercise_id: uuid.UUID) -> Exercise:
    exercise = await session.scalar(
        select(Exercise)
        .join(Lesson, Lesson.id == Exercise.lesson_id)
        .where(Exercise.id == exercise_id, Lesson.published.is_(True))
    )
    if exercise is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="exercise not found")
    return exercise


def to_exercise_out(row: Exercise) -> ExerciseOut:
    merged = {**row.payload, **row.answer}
    return ExerciseOut(
        id=row.id, order_index=row.order_index, exercise=ExerciseAdapter.validate_python(merged)
    )
