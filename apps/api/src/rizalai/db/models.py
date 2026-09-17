"""SQLAlchemy models. One class per table in docs/architecture.md section 3.

IDs for authored content (units, lessons, exercises) are deterministic
uuid5 values derived from slugs, so re-seeding never creates duplicates and
progress rows keep pointing at the same exercises across deploys.
"""

import uuid
from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

EMBEDDING_DIMS = 1024  # bge-m3 dense size


class Base(DeclarativeBase):
    pass


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def _created_at() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class User(Base):
    __tablename__ = "users"

    # Equals auth.users.id on Supabase. No FK locally; see docs/tech-debt.md item 1.
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)
    total_xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    streak_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_activity_date: Mapped[date | None] = mapped_column(Date)
    hearts: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    hearts_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    current_unit_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = _created_at()


class Unit(Base):
    __tablename__ = "units"

    id: Mapped[uuid.UUID] = _uuid_pk()
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = _created_at()


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[uuid.UUID] = _uuid_pk()
    unit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("units.id", ondelete="CASCADE"), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    vignette: Mapped[list[dict[str, object]]] = mapped_column(JSONB, default=list, nullable=False)
    grammar_focus: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    target_vocab: Mapped[list[dict[str, object]]] = mapped_column(JSONB, default=list, nullable=False)
    source_passage_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), default=list, nullable=False
    )
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (UniqueConstraint("unit_id", "order_index", name="uq_lessons_unit_order"),)


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[uuid.UUID] = _uuid_pk()
    lesson_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    answer: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    xp: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    created_at: Mapped[datetime] = _created_at()

    __table_args__ = (UniqueConstraint("lesson_id", "order_index", name="uq_exercises_lesson_order"),)


class SourcePassage(Base):
    __tablename__ = "source_passages"

    id: Mapped[uuid.UUID] = _uuid_pk()
    work: Mapped[str] = mapped_column(String(20), nullable=False)  # noli | fili | essay | letter
    language: Mapped[str] = mapped_column(String(8), nullable=False)  # es | tl | en
    translator: Mapped[str | None] = mapped_column(String(40))
    chapter: Mapped[int] = mapped_column(Integer, nullable=False)
    paragraph_index: Mapped[int] = mapped_column(Integer, nullable=False)
    passage_group_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    text: Mapped[str] = mapped_column(Text, nullable=False)
    char_start: Mapped[int] = mapped_column(Integer, nullable=False)
    char_end: Mapped[int] = mapped_column(Integer, nullable=False)
    tags: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict, nullable=False)
    tag_source: Mapped[str] = mapped_column(String(10), default="none", nullable=False)  # none|llm|human
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIMS))
    sparse: Mapped[dict[str, float] | None] = mapped_column(JSONB)
    embedding_model: Mapped[str | None] = mapped_column(String(80))
    license_note: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = _created_at()

    __table_args__ = (
        UniqueConstraint("work", "language", "chapter", "paragraph_index", name="uq_passage_locator"),
        Index("ix_passages_work_lang_chapter", "work", "language", "chapter"),
        Index("ix_passages_group", "passage_group_id"),
    )


class ExerciseAttempt(Base):
    __tablename__ = "exercise_attempts"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    response: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = _created_at()

    __table_args__ = (Index("ix_attempts_user_lesson_time", "user_id", "lesson_id", "created_at"),)


class UserProgress(Base):
    __tablename__ = "user_progress"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    best_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    xp_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lesson_version: Mapped[str] = mapped_column(String(64), nullable=False)


class ReviewQueue(Base):
    __tablename__ = "review_queue"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False
    )
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    stability: Mapped[float] = mapped_column(Float, nullable=False)
    difficulty: Mapped[float] = mapped_column(Float, nullable=False)
    last_review: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lapses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    state: Mapped[str] = mapped_column(String(12), nullable=False)  # learning|review|relearning
    step: Mapped[int | None] = mapped_column(Integer)  # FSRS learning step within a state

    __table_args__ = (
        UniqueConstraint("user_id", "exercise_id", name="uq_review_user_exercise"),
        Index("ix_review_user_due", "user_id", "due_at"),
    )


class GeneratedContentCache(Base):
    __tablename__ = "generated_content_cache"

    id: Mapped[uuid.UUID] = _uuid_pk()
    kind: Mapped[str] = mapped_column(String(20), nullable=False)  # reflection | hint | drill
    cache_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    content: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    citations_valid: Mapped[bool] = mapped_column(Boolean, nullable=False)
    judge_score: Mapped[float | None] = mapped_column(Numeric(4, 2))
    status: Mapped[str] = mapped_column(String(12), nullable=False)  # published|rejected|fallback
    model: Mapped[str] = mapped_column(String(80), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = _created_at()
