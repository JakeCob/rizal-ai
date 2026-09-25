"""POST /attempts and POST /lessons/{id}/complete (DECISIONS.md D15).

Attempts are fire-and-forget from the client and graded here from the
stored answer key. Completion re-grades the latest attempt per exercise made
since the previous completion, awards XP, updates streak and hearts, upserts
progress, and schedules every exercise in the review queue, all in one
transaction.
"""

import uuid
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from rizalai.auth.deps import CurrentUser
from rizalai.db.models import Exercise, ExerciseAttempt, UserProgress
from rizalai.db.session import get_session
from rizalai.lessons.service import get_published_exercise, get_published_lesson
from rizalai.progress.rules import apply_regen, grade_response, local_today, next_streak, spend_heart
from rizalai.srs.scheduler import record_review

router = APIRouter(tags=["progress"])
Session = Annotated[AsyncSession, Depends(get_session)]


class AttemptIn(BaseModel):
    exercise_id: uuid.UUID
    correct: bool = Field(description="The client's local grade; ignored, the server grades the response")
    response: dict[str, Any]
    duration_ms: int = Field(ge=0, le=3_600_000)


class AttemptOut(BaseModel):
    correct: bool
    hearts: int


class ResultOut(BaseModel):
    exercise_id: uuid.UUID
    correct: bool
    xp: int


class CompleteOut(BaseModel):
    lesson_id: uuid.UUID
    xp_earned: int
    total_xp: int
    streak_count: int
    hearts: int
    results: list[ResultOut]


@router.post("/attempts", response_model=AttemptOut, status_code=status.HTTP_202_ACCEPTED)
async def post_attempt(body: AttemptIn, user: CurrentUser, session: Session) -> AttemptOut:
    exercise = await get_published_exercise(session, body.exercise_id)
    now = datetime.now(UTC)
    correct = grade_response(exercise.type, exercise.answer, body.response)
    if correct:
        apply_regen(user, now)
    else:
        spend_heart(user, now)
    session.add(
        ExerciseAttempt(
            user_id=user.id,
            exercise_id=exercise.id,
            lesson_id=exercise.lesson_id,
            correct=correct,
            response=body.response,
            duration_ms=body.duration_ms,
            created_at=now,  # one clock per request; completion compares against it
        )
    )
    await session.commit()
    return AttemptOut(correct=correct, hearts=user.hearts)


async def _latest_attempts_since(
    session: AsyncSession, user_id: uuid.UUID, lesson_id: uuid.UUID, since: datetime | None
) -> dict[uuid.UUID, ExerciseAttempt]:
    stmt = (
        select(ExerciseAttempt)
        .where(ExerciseAttempt.user_id == user_id, ExerciseAttempt.lesson_id == lesson_id)
        .order_by(ExerciseAttempt.created_at.desc())
    )
    if since is not None:
        stmt = stmt.where(ExerciseAttempt.created_at > since)
    latest: dict[uuid.UUID, ExerciseAttempt] = {}
    for attempt in await session.scalars(stmt):
        latest.setdefault(attempt.exercise_id, attempt)
    return latest


@router.post("/lessons/{lesson_id}/complete", response_model=CompleteOut)
async def complete_lesson(lesson_id: uuid.UUID, user: CurrentUser, session: Session) -> CompleteOut:
    lesson = await get_published_lesson(session, lesson_id)
    exercises = (
        await session.scalars(
            select(Exercise).where(Exercise.lesson_id == lesson_id).order_by(Exercise.order_index)
        )
    ).all()
    progress = await session.get(UserProgress, (user.id, lesson_id))
    since = progress.completed_at if progress else None
    latest = await _latest_attempts_since(session, user.id, lesson_id, since)
    if not latest:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="no attempts since last completion")

    now = datetime.now(UTC)
    results: list[ResultOut] = []
    for exercise in exercises:
        attempt = latest.get(exercise.id)
        correct = attempt is not None and grade_response(exercise.type, exercise.answer, attempt.response)
        results.append(ResultOut(exercise_id=exercise.id, correct=correct, xp=exercise.xp if correct else 0))
        await record_review(session, user.id, exercise.id, correct, now)

    xp_earned = sum(r.xp for r in results)
    correct_count = sum(1 for r in results if r.correct)
    score = round(100.0 * correct_count / len(exercises), 2) if exercises else 0.0

    apply_regen(user, now)
    today = local_today(user.timezone, now)
    user.streak_count = next_streak(user.streak_count, user.last_activity_date, today)
    user.last_activity_date = today
    user.total_xp += xp_earned

    values = {
        "user_id": user.id,
        "lesson_id": lesson_id,
        "attempts": 1,
        "completed_at": now,
        "best_score": score,
        "xp_earned": xp_earned,
        "lesson_version": lesson.version,
    }
    stmt = insert(UserProgress).values(**values)
    stmt = stmt.on_conflict_do_update(
        index_elements=["user_id", "lesson_id"],
        set_={
            "attempts": UserProgress.attempts + 1,
            "completed_at": now,
            "best_score": _greatest(UserProgress.best_score, score),
            "xp_earned": UserProgress.xp_earned + xp_earned,
            "lesson_version": lesson.version,
        },
    )
    await session.execute(stmt)
    await session.commit()

    return CompleteOut(
        lesson_id=lesson_id,
        xp_earned=xp_earned,
        total_xp=user.total_xp,
        streak_count=user.streak_count,
        hearts=user.hearts,
        results=results,
    )


def _greatest(column: Any, value: float) -> Any:
    from sqlalchemy import func

    return func.greatest(column, value)
