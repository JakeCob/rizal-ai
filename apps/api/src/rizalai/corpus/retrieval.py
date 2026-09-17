"""Passage retrieval for the reflection pipeline.

The card's passages are pinned by the lesson (metadata lookup, D19). Style
context is a few more Tagalog paragraphs from the same chapters, never
citable. Semantic and hybrid search arrive with the extras
(docs/tech-debt.md item 8).
"""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rizalai.db.models import SourcePassage

LANGUAGE_ORDER = {"es": 0, "tl": 1, "en": 2}


async def pinned_passages(session: AsyncSession, ids: Sequence[uuid.UUID]) -> list[SourcePassage]:
    if not ids:
        return []
    rows = (await session.scalars(select(SourcePassage).where(SourcePassage.id.in_(list(ids))))).all()
    return sorted(rows, key=lambda r: (LANGUAGE_ORDER.get(r.language, 9), r.chapter, r.paragraph_index))


async def style_context(
    session: AsyncSession,
    *,
    work: str,
    language: str,
    chapters: Sequence[int],
    exclude: Sequence[uuid.UUID],
    limit: int = 3,
) -> list[SourcePassage]:
    if not chapters:
        return []
    stmt = (
        select(SourcePassage)
        .where(
            SourcePassage.work == work,
            SourcePassage.language == language,
            SourcePassage.chapter.in_(list(chapters)),
            SourcePassage.tags["kind"].astext == "body",
        )
        .order_by(SourcePassage.chapter, SourcePassage.paragraph_index)
    )
    if exclude:
        stmt = stmt.where(SourcePassage.id.not_in(list(exclude)))
    rows = (await session.scalars(stmt)).all()
    # Prefer longer paragraphs: they carry more of the voice than one-line dialogue.
    rows = sorted(rows, key=lambda r: -len(r.text))
    return rows[:limit]
