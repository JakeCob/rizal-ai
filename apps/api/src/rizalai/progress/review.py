"""GET /review/due and POST /review/answer (SPEC.md 6.6).

A practice session is a run of review answers within a 30 minute window.
Every tenth answer in a session refills hearts, which is the
practice-to-refill flow of DECISIONS.md D16.
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from rizalai.auth.deps import CurrentUser
from rizalai.contracts.lesson import ExerciseOut
from rizalai.db.models import Exercise, ExerciseAttempt, ReviewQueue
from rizalai.db.session import get_session
from rizalai.lessons.router import to_exercise_out
from rizalai.progress.rules import MAX_HEARTS, apply_regen, grade_response
from rizalai.srs.scheduler import record_review

router = APIRouter(prefix="/review", tags=["review"])
Session = Annotated[AsyncSession, Depends(get_session)]

SESSION_WINDOW = timedelta(minutes=30)
REFILL_EVERY = 10
DUE_LIMIT = 10


class ReviewItemOut(BaseModel):
    exercise: ExerciseOut
    due_at: datetime
    state: str
    reps: int


class ReviewDueOut(BaseModel):
    items: list[ReviewItemOut]


class ReviewAnswerIn(BaseModel):
    exercise_id: uuid.UUID
    response: dict[str, Any]
    duration_ms: int = 0


class ReviewAnswerOut(BaseModel):
    correct: bool
    hearts: int
    session_answered: int
    next_due_at: datetime
    state: str


@router.get("/due", response_model=ReviewDueOut)
async def due(user: CurrentUser, session: Session) -> ReviewDueOut:
    now = datetime.now(UTC)
    rows = await session.execute(
        select(ReviewQueue, Exercise)
        .join(Exercise, Exercise.id == ReviewQueue.exercise_id)
        .where(ReviewQueue.user_id == user.id, ReviewQueue.due_at <= now)
        .order_by(ReviewQueue.due_at)
        .limit(DUE_LIMIT)
    )
    items = [
        ReviewItemOut(
            exercise=to_exercise_out(exercise), due_at=item.due_at, state=item.state, reps=item.reps
        )
        for item, exercise in rows
    ]
    return ReviewDueOut(items=items)


@router.post("/answer", response_model=ReviewAnswerOut)
async def answer(body: ReviewAnswerIn, user: CurrentUser, session: Session) -> ReviewAnswerOut:
    exercise = await session.get(Exercise, body.exercise_id)
    if exercise is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="exercise not found")
    now = datetime.now(UTC)
    correct = grade_response(exercise.type, exercise.answer, body.response)
    item = await record_review(session, user.id, exercise.id, correct, now)
    session.add(
        ExerciseAttempt(
            user_id=user.id,
            exercise_id=exercise.id,
            lesson_id=exercise.lesson_id,
            correct=correct,
            response=body.response,
            duration_ms=body.duration_ms,
            kind="review",
            created_at=now,
        )
    )
    await session.flush()
    answered = await session.scalar(
        select(func.count())
        .select_from(ExerciseAttempt)
        .where(
            ExerciseAttempt.user_id == user.id,
            ExerciseAttempt.kind == "review",
            ExerciseAttempt.created_at > now - SESSION_WINDOW,
        )
    )
    session_answered = int(answered or 0)
    apply_regen(user, now)
    if session_answered % REFILL_EVERY == 0:
        user.hearts = MAX_HEARTS
        user.hearts_updated_at = now
    await session.commit()
    return ReviewAnswerOut(
        correct=correct,
        hearts=user.hearts,
        session_answered=session_answered,
        next_due_at=item.due_at,
        state=item.state,
    )
