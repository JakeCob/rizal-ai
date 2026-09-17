"""Ingest a parsed edition into source_passages and embed it. Idempotent:
rows are keyed by (work, language, chapter, paragraph_index) and re-running
updates text and offsets in place."""

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy import literal_column, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from rizalai.corpus.embeddings import Embedder
from rizalai.corpus.gutenberg import EditionSpec, ParsedPassage, parse_edition
from rizalai.db.models import SourcePassage

log = logging.getLogger(__name__)


@dataclass
class IngestReport:
    parsed: int = 0
    inserted: int = 0
    updated: int = 0
    embedded: int = 0


def _row_values(p: ParsedPassage, license_note: str) -> dict[str, object]:
    return {
        "work": p.work,
        "language": p.language,
        "translator": p.translator,
        "chapter": p.chapter,
        "paragraph_index": p.paragraph_index,
        "text": p.text,
        "char_start": p.char_start,
        "char_end": p.char_end,
        "tags": {"chapter_title": p.chapter_title, "kind": "footnote" if p.is_footnote else "body"},
        "tag_source": "none",
        "license_note": license_note,
    }


async def upsert_passages(
    session: AsyncSession, spec: EditionSpec, passages: list[ParsedPassage]
) -> IngestReport:
    report = IngestReport(parsed=len(passages))
    for p in passages:
        values = _row_values(p, spec.license_note)
        stmt: Any = (
            insert(SourcePassage)
            .values(**values)
            .on_conflict_do_update(
                constraint="uq_passage_locator",
                set_={
                    k: values[k]
                    for k in ("translator", "text", "char_start", "char_end", "tags", "license_note")
                },
            )
            .returning(literal_column("(xmax = 0)").label("inserted"))
        )
        inserted = await session.scalar(stmt)
        if inserted:
            report.inserted += 1
        else:
            report.updated += 1
    return report


async def embed_missing(
    session: AsyncSession, spec: EditionSpec, embedder: Embedder, batch_size: int = 32
) -> int:
    model = getattr(embedder, "model", "unknown")
    rows = (
        await session.scalars(
            select(SourcePassage)
            .where(
                SourcePassage.work == spec.work,
                SourcePassage.language == spec.language,
                (SourcePassage.embedding.is_(None)) | (SourcePassage.embedding_model != model),
            )
            .order_by(SourcePassage.chapter, SourcePassage.paragraph_index)
        )
    ).all()
    done = 0
    for start in range(0, len(rows), batch_size):
        batch = rows[start : start + batch_size]
        vectors = embedder.embed([r.text for r in batch])
        for row, vec in zip(batch, vectors, strict=True):
            await session.execute(
                update(SourcePassage)
                .where(SourcePassage.id == row.id)
                .values(embedding=vec.dense, sparse=vec.sparse, embedding_model=vec.model)
            )
        done += len(batch)
        log.info("embedded %d/%d %s passages", done, len(rows), spec.key)
    return done


async def ingest_text(
    session: AsyncSession,
    spec: EditionSpec,
    raw: str,
    embedder: Embedder | None,
    batch_size: int = 32,
) -> IngestReport:
    passages = parse_edition(spec, raw)
    report = await upsert_passages(session, spec, passages)
    if embedder is not None:
        report.embedded = await embed_missing(session, spec, embedder, batch_size)
    await session.commit()
    return report
