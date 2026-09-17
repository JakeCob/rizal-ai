"""Contract for GET /lessons/{id}/reflection: the "In Rizal's voice" card."""

import uuid
from typing import Literal

from pydantic import BaseModel, Field


class QuotedSpan(BaseModel):
    """A span of the reflection that carries Rizal's byline. Must be a
    verbatim substring of the cited passage (DECISIONS.md D03)."""

    text: str = Field(min_length=1)
    passage_id: uuid.UUID


class ReflectionDraft(BaseModel):
    """What the model returns. Tagalog is written first (D02)."""

    tl: str = Field(min_length=1, description="Reflection in modern Tagalog, in Rizal's voice")
    en: str = Field(min_length=1, description="English rendering of the Tagalog reflection")
    quoted_spans: list[QuotedSpan] = Field(default_factory=list)


class PassageOut(BaseModel):
    id: uuid.UUID
    chapter: int
    paragraph_index: int
    text: str


class LayerOut(BaseModel):
    language: Literal["es", "tl", "en"]
    translator: str | None
    label: str
    passages: list[PassageOut]


class ReflectionOut(BaseModel):
    lesson_id: uuid.UUID
    status: Literal["published", "fallback"]
    layers: list[LayerOut]
    reflection: ReflectionDraft | None
    model: str
    prompt_version: str
