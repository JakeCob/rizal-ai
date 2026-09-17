"""Lesson contract.

LessonContent is the shape of a lesson YAML file under content/. LessonOut is
what GET /lessons/{id} returns: the same content plus database ids, the
content hash as version, and resolved source passage ids.

Exercise is a discriminated union on `type`. Adding word_picture later is a
new member, not a change to existing members.
"""

import uuid
from collections import Counter
from typing import Annotated, Literal

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


def _check_bank_covers_answer(answer_tokens: list[str], bank: list[str]) -> None:
    missing = Counter(answer_tokens) - Counter(bank)
    if missing:
        raise ValueError(f"answer tokens not covered by bank: {sorted(missing)}")


class SentenceAssembly(ExerciseBase):
    """Build the Tagalog line from a word bank, given the English."""

    type: Literal["sentence_assembly"]
    prompt_en: str = Field(min_length=1)
    answer_tokens: list[str] = Field(min_length=1)
    bank: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def bank_covers_answer(self) -> "SentenceAssembly":
        _check_bank_covers_answer(self.answer_tokens, self.bank)
        return self


class TranslateLine(ExerciseBase):
    """Translate a line in either direction from a word bank."""

    type: Literal["translate_line"]
    direction: Literal["tl_to_en", "en_to_tl"]
    prompt: str = Field(min_length=1)
    answer_tokens: list[str] = Field(min_length=1)
    bank: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def bank_covers_answer(self) -> "TranslateLine":
        _check_bank_covers_answer(self.answer_tokens, self.bank)
        return self


class ListenTap(ExerciseBase):
    """Hear a Tagalog line, tap the words heard."""

    type: Literal["listen_tap"]
    audio_url: str | None = None
    transcript_tl: str = Field(min_length=1)
    answer_tokens: list[str] = Field(min_length=1)
    bank: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def bank_covers_answer(self) -> "ListenTap":
        _check_bank_covers_answer(self.answer_tokens, self.bank)
        return self


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
