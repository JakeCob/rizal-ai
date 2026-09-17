"""Internal shapes for the generation pipeline. The API contract lives in
rizalai.contracts.reflection and is re-exported here for convenience."""

import uuid

from pydantic import BaseModel

from rizalai.contracts.reflection import (
    LayerOut,
    PassageOut,
    QuotedSpan,
    ReflectionDraft,
    ReflectionOut,
)

__all__ = ["LayerOut", "PassageForPrompt", "PassageOut", "QuotedSpan", "ReflectionDraft", "ReflectionOut"]


class PassageForPrompt(BaseModel):
    id: uuid.UUID
    language: str
    chapter: int
    paragraph_index: int
    text: str
