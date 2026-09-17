"""FSRS scheduling for review_queue rows.

A correct answer is rated Good, a wrong one Again. FSRS owns stability,
difficulty, due, state, and step; reps and lapses are counted here because
the library does not track them.
"""

import uuid
from datetime import datetime

from fsrs import Card, Rating, Scheduler, State
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rizalai.db.models import ReviewQueue

_scheduler = Scheduler()

STATE_TO_NAME = {State.Learning: "learning", State.Review: "review", State.Relearning: "relearning"}
NAME_TO_STATE = {v: k for k, v in STATE_TO_NAME.items()}


def _card(row: ReviewQueue | None) -> Card:
    if row is None:
        return Card()
    return Card(
        state=NAME_TO_STATE.get(row.state, State.Learning),
        step=row.step,
        stability=row.stability,
        difficulty=row.difficulty,
        due=row.due_at,
        last_review=row.last_review,
    )


async def record_review(
    session: AsyncSession, user_id: uuid.UUID, exercise_id: uuid.UUID, correct: bool, now: datetime
) -> ReviewQueue:
    row = await session.scalar(
        select(ReviewQueue).where(ReviewQueue.user_id == user_id, ReviewQueue.exercise_id == exercise_id)
    )
    previous_state = row.state if row else "new"
    card, _log = _scheduler.review_card(_card(row), Rating.Good if correct else Rating.Again, now)

    if row is None:
        row = ReviewQueue(user_id=user_id, exercise_id=exercise_id, reps=0, lapses=0)
        session.add(row)
    row.due_at = card.due
    row.stability = float(card.stability or 0.0)
    row.difficulty = float(card.difficulty or 0.0)
    row.last_review = card.last_review
    row.step = card.step
    row.state = STATE_TO_NAME[card.state]
    row.reps += 1
    if not correct and previous_state == "review":
        row.lapses += 1
    return row
