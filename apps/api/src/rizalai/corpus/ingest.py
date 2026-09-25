"""Ingest a parsed edition into source_passages and embed it. Idempotent:
rows are keyed by (work, language, chapter, paragraph_index) and re-running
updates text and offsets in place.

The three editions are committed under apps/api/data/raw (D37) with pinned
digests, so production passages are byte-identical to dev's and the hand
alignment of pinned refs cannot drift under a fresh download. Upserts go in
batches, so a run over a remote proxy takes minutes, not hours."""

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import func, literal_column, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from rizalai.corpus.embeddings import Embedder
from rizalai.corpus.gutenberg import EDITIONS, EditionSpec, ParsedPassage, fetch_gutenberg_text, parse_edition
from rizalai.db.models import SourcePassage

log = logging.getLogger(__name__)

# Relative to the API's working directory (apps/api locally, /app in the image).
RAW_DIR = Path("data/raw")
RAW_FILES = {
    "noli_es": "noli_es_rizal_1887.txt",
    "noli_tl": "noli_tl_poblete_1909.txt",
    "noli_en": "noli_en_derbyshire_1912.txt",
}
RAW_SHA256 = {
    "noli_es": "a1e437097e5c6b86baa0db08c3d091b76d46f347db5f1e1dd14bdfb1d3f84f8e",
    "noli_tl": "43ef048e077f5a4080f6887b36ea26328ae1ce192891a20f28bf58909b06119a",
    "noli_en": "edaff46d61e92a7eeea5236280d2c9db7a304210379fa2d65148d097ad02b59e",
}
UPSERT_BATCH = 500
UPDATED_COLUMNS = ("translator", "text", "char_start", "char_end", "tags", "license_note")


def raw_path(key: str, raw_dir: Path = RAW_DIR) -> Path:
    """Where the committed text for an edition key lives."""
    return raw_dir / RAW_FILES[key]


class CorpusFileError(RuntimeError):
    """The committed corpus text is missing or is not the pinned file."""


def load_edition_text(
    key: str, file: Path | None = None, raw_dir: Path = RAW_DIR, *, download: bool = False
) -> str:
    """The text `rizalai ingest` reads. An explicit file is read as given.
    Otherwise the committed file must exist and match its pinned digest. A
    fresh Gutenberg copy is fetched only on request, and saved beside the
    pinned file under another name, never over it."""
    if file is not None:
        return file.read_text(encoding="utf-8", errors="replace")
    if download:
        text = fetch_gutenberg_text(EDITIONS[key].gutenberg_id)
        target = raw_dir / f"{key}.download.txt"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        log.warning("downloaded %s to %s; it is not the pinned text", key, target)
        return text
    path = raw_path(key, raw_dir)
    if not path.is_file():
        raise CorpusFileError(f"{path} is missing: restore it from git, or pass --download for a fresh copy")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != RAW_SHA256[key]:
        raise CorpusFileError(f"{path} does not match its pinned sha256: restore it from git")
    return data.decode("utf-8", errors="replace")


@dataclass
class IngestReport:
    parsed: int = 0
    inserted: int = 0
    updated: int = 0
    embedded: int = 0
    skipped: bool = False


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
    for start in range(0, len(passages), UPSERT_BATCH):
        rows = [_row_values(p, spec.license_note) for p in passages[start : start + UPSERT_BATCH]]
        base = insert(SourcePassage).values(rows)
        stmt: Any = base.on_conflict_do_update(
            constraint="uq_passage_locator",
            set_={k: getattr(base.excluded, k) for k in UPDATED_COLUMNS},
        ).returning(literal_column("(xmax = 0)").label("inserted"))
        for inserted in (await session.scalars(stmt)).all():
            if inserted:
                report.inserted += 1
            else:
                report.updated += 1
    return report


async def edition_row_count(session: AsyncSession, spec: EditionSpec) -> int:
    stmt = select(func.count()).select_from(SourcePassage)
    stmt = stmt.where(SourcePassage.work == spec.work, SourcePassage.language == spec.language)
    return int(await session.scalar(stmt) or 0)


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
    *,
    skip_if_present: bool = False,
) -> IngestReport:
    """Parse and upsert one edition. With skip_if_present, an edition whose
    row count already equals the parsed paragraph count is left untouched."""
    passages = parse_edition(spec, raw)
    if skip_if_present and await edition_row_count(session, spec) == len(passages):
        report = IngestReport(parsed=len(passages), skipped=True)
    else:
        report = await upsert_passages(session, spec, passages)
    if embedder is not None:
        report.embedded = await embed_missing(session, spec, embedder, batch_size)
    await session.commit()
    return report
