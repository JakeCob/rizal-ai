"""Lesson contract.

LessonContent is the shape of a lesson YAML file under content/. LessonOut is
what GET /lessons/{id} returns: the same content plus database ids, the
content hash as version, and resolved source passage ids.

Exercise is a discriminated union on `type`. Adding word_picture later is a
new member, not a change to existing members.
"""

import uuid
from collections import Counter
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator

VIGNETTE_BEATS = (4, 8)
EXERCISES_PER_LESSON = (6, 12)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Beat(StrictModel):
    line_id: str = Field(min_length=1, max_length=20)
    speaker: str | None = None
    tl: str = Field(min_length=1)
    en: str = Field(min_length=1)
    audio_url: str | None = None
    exercise_after: str | None = Field(default=None, description="Exercise key to run after this beat")


class VocabItem(StrictModel):
    tl: str
    en: str
    pos: str | None = None
    note: str | None = None


class PassageRef(StrictModel):
    """Locator for a source passage, resolved to an id at seed time."""

    work: Literal["noli", "fili", "essay", "letter"]
    language: Literal["es", "tl", "en"]
    chapter: int = Field(ge=0)
    paragraph_index: int = Field(ge=0)
    group: str | None = Field(
        default=None,
        max_length=40,
        description="Refs sharing a group within a lesson are the same passage in different languages",
    )


class ExerciseBase(StrictModel):
    key: str = Field(min_length=1, max_length=20, description="Stable key within the lesson")
    xp: int = Field(default=10, ge=0, le=100)


ACCEPTED_ORDERS_DESCRIPTION = (
    "Other natural orders graded correct besides answer_tokens (DECISIONS.md D34). "
    "Each is non-empty, differs from answer_tokens and from the other orders, and is "
    "covered by the bank. answer_tokens stays the order shown on the feedback sheet."
)


def _check_covered(label: str, tokens: list[str], bank: list[str]) -> None:
    """Bank coverage as a multiset, case-sensitive so tiles render as authored."""
    missing = Counter(tokens) - Counter(bank)
    if missing:
        raise ValueError(f"{label} not covered by bank: {sorted(missing)}")


def _folded(tokens: list[str]) -> list[str]:
    return [t.lower() for t in tokens]


class TokenExercise(ExerciseBase):
    """Fields and checks shared by the three token exercises. Only grading
    folds case (D34), so distinctness is judged after lowercasing while bank
    coverage stays exact."""

    answer_tokens: list[str] = Field(min_length=1)
    accepted_orders: list[list[str]] = Field(default_factory=list, description=ACCEPTED_ORDERS_DESCRIPTION)
    bank: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def check_tokens(self) -> Self:
        _check_covered("answer tokens", self.answer_tokens, self.bank)
        seen = [_folded(self.answer_tokens)]
        for order in self.accepted_orders:
            if not order:
                raise ValueError("accepted order is empty")
            folded = _folded(order)
            if folded == seen[0]:
                raise ValueError(f"accepted order {order} repeats answer_tokens (letter case is ignored)")
            if folded in seen:
                raise ValueError(f"accepted order {order} is a duplicate (letter case is ignored)")
            _check_covered(f"accepted order {order}", order, self.bank)
            seen.append(folded)
        return self


class SentenceAssembly(TokenExercise):
    """Build the Tagalog line from a word bank, given the English."""

    type: Literal["sentence_assembly"]
    prompt_en: str = Field(min_length=1)


class TranslateLine(TokenExercise):
    """Translate a line in either direction from a word bank."""

    type: Literal["translate_line"]
    direction: Literal["tl_to_en", "en_to_tl"]
    prompt: str = Field(min_length=1)


class ListenTap(TokenExercise):
    """Hear a Tagalog line, tap the words heard."""

    type: Literal["listen_tap"]
    audio_url: str | None = None
    transcript_tl: str = Field(min_length=1)


class ComprehensionMC(ExerciseBase):
    """Multiple choice about the passage."""

    type: Literal["comprehension_mc"]
    question: str = Field(min_length=1)
    options: list[str] = Field(min_length=2, max_length=4)
    correct_index: int = Field(ge=0)
    explanation: str | None = None

    @model_validator(mode="after")
    def index_in_range(self) -> "ComprehensionMC":
        if self.correct_index >= len(self.options):
            raise ValueError("correct_index is out of range for options")
        return self


Exercise = Annotated[
    SentenceAssembly | TranslateLine | ListenTap | ComprehensionMC,
    Field(discriminator="type"),
]
ExerciseAdapter: TypeAdapter[Exercise] = TypeAdapter(Exercise)

ExerciseType = Literal["sentence_assembly", "translate_line", "listen_tap", "comprehension_mc"]


class LessonContent(StrictModel):
    """One lesson YAML file. Unpublished lessons may be stubs."""

    slug: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$", max_length=80)
    title: str = Field(min_length=1, max_length=160)
    published: bool = False
    estimated_minutes: int = Field(default=5, ge=1, le=15)
    grammar_focus: list[str] = Field(default_factory=list)
    target_vocab: list[VocabItem] = Field(default_factory=list)
    source_passages: list[PassageRef] = Field(default_factory=list)
    vignette: list[Beat] = Field(default_factory=list)
    exercises: list[Exercise] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_structure(self) -> "LessonContent":
        keys = [e.key for e in self.exercises]
        if len(keys) != len(set(keys)):
            raise ValueError("exercise keys must be unique within a lesson")
        line_ids = [b.line_id for b in self.vignette]
        if len(line_ids) != len(set(line_ids)):
            raise ValueError("beat line_ids must be unique within a lesson")
        for beat in self.vignette:
            if beat.exercise_after is not None and beat.exercise_after not in keys:
                raise ValueError(f"beat {beat.line_id} exercise_after references unknown key")
        if self.published:
            lo, hi = VIGNETTE_BEATS
            if not lo <= len(self.vignette) <= hi:
                raise ValueError(f"a published lesson needs {lo} to {hi} vignette beats")
            lo, hi = EXERCISES_PER_LESSON
            if not lo <= len(self.exercises) <= hi:
                raise ValueError(f"a published lesson needs {lo} to {hi} exercises")
        return self


class ExerciseOut(BaseModel):
    id: uuid.UUID
    order_index: int
    exercise: Exercise


class LessonOut(BaseModel):
    id: uuid.UUID
    unit_id: uuid.UUID
    slug: str
    title: str
    version: str
    estimated_minutes: int
    grammar_focus: list[str]
    target_vocab: list[VocabItem]
    source_passage_ids: list[uuid.UUID]
    vignette: list[Beat]
    exercises: list[ExerciseOut]
