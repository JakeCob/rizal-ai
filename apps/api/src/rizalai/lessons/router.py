import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rizalai.auth.deps import CurrentUser
from rizalai.contracts.lesson import Beat, ExerciseAdapter, ExerciseOut, LessonOut, VocabItem
from rizalai.contracts.tree import LessonStatus, Tree, TreeLesson, TreeUnit
from rizalai.db.models import Exercise, Lesson, Unit, UserProgress
from rizalai.db.session import get_session

router = APIRouter(tags=["lessons"])

Session = Annotated[AsyncSession, Depends(get_session)]


def to_exercise_out(row: Exercise) -> ExerciseOut:
    merged = {**row.payload, **row.answer}
    return ExerciseOut(
        id=row.id, order_index=row.order_index, exercise=ExerciseAdapter.validate_python(merged)
    )


@router.get("/lessons/{lesson_id}", response_model=LessonOut)
async def get_lesson(lesson_id: uuid.UUID, user: CurrentUser, session: Session) -> LessonOut:
    lesson = await session.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="lesson not found")
    rows = await session.scalars(
        select(Exercise).where(Exercise.lesson_id == lesson_id).order_by(Exercise.order_index)
    )
    return LessonOut(
        id=lesson.id,
        unit_id=lesson.unit_id,
        slug=lesson.slug,
        title=lesson.title,
        version=lesson.version,
        estimated_minutes=lesson.estimated_minutes,
        grammar_focus=list(lesson.grammar_focus),
        target_vocab=[VocabItem.model_validate(v) for v in lesson.target_vocab],
        source_passage_ids=list(lesson.source_passage_ids),
        vignette=[Beat.model_validate(b) for b in lesson.vignette],
        exercises=[to_exercise_out(row) for row in rows],
    )


@router.get("/tree", response_model=Tree)
async def get_tree(user: CurrentUser, session: Session) -> Tree:
    units = (await session.scalars(select(Unit).order_by(Unit.order_index))).all()
    lessons = (await session.scalars(select(Lesson).order_by(Lesson.unit_id, Lesson.order_index))).all()
    done_ids = set(
        await session.scalars(
            select(UserProgress.lesson_id).where(
                UserProgress.user_id == user.id, UserProgress.completed_at.is_not(None)
            )
        )
    )

    xp_by_lesson: dict[uuid.UUID, int] = {}
    xp_rows = await session.execute(select(Exercise.lesson_id, Exercise.xp))
    for lesson_id_, xp in xp_rows:
        xp_by_lesson[lesson_id_] = xp_by_lesson.get(lesson_id_, 0) + xp

    active_assigned = False
    by_unit: dict[uuid.UUID, list[TreeLesson]] = {u.id: [] for u in units}
    for lesson in lessons:
        status_: LessonStatus
        if lesson.id in done_ids:
            status_ = "done"
        elif lesson.published and not active_assigned:
            status_ = "active"
            active_assigned = True
        else:
            status_ = "locked"
        by_unit.setdefault(lesson.unit_id, []).append(
            TreeLesson(
                id=lesson.id,
                slug=lesson.slug,
                title=lesson.title,
                order_index=lesson.order_index,
                status=status_,
                xp_reward=xp_by_lesson.get(lesson.id, 0),
                estimated_minutes=lesson.estimated_minutes,
            )
        )

    return Tree(
        units=[
            TreeUnit(id=u.id, slug=u.slug, title=u.title, order_index=u.order_index, lessons=by_unit[u.id])
            for u in units
        ]
    )
