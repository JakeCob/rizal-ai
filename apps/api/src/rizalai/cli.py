"""Operator commands: seed content, export contracts, ingest corpus.

Usage:
  uv run rizalai seed
  uv run rizalai export-contracts [path]
  uv run rizalai ingest noli_tl [--file PATH] [--no-embed]
"""

import argparse
import asyncio
import logging
from pathlib import Path

from rizalai.config import get_settings
from rizalai.content.seed import seed_content
from rizalai.contracts.export import export_schema
from rizalai.corpus.embeddings import embedder_from_settings
from rizalai.corpus.gutenberg import EDITIONS, fetch_gutenberg_text
from rizalai.corpus.ingest import ingest_text
from rizalai.db.session import dispose_engine, get_session_factory

RAW_DIR = Path("data/raw")


async def _seed(content_dir: Path) -> None:
    async with get_session_factory()() as session:
        report = await seed_content(session, content_dir)
    await dispose_engine()
    print(
        f"seeded {report.units} units, {report.lessons} lessons, {report.exercises} exercises; "
        f"{report.unresolved_passages} passage refs unresolved"
    )


def _load_edition_text(key: str, file: Path | None) -> str:
    spec = EDITIONS[key]
    path = file or RAW_DIR / f"{key}.txt"
    if path.exists():
        return path.read_text(encoding="utf-8", errors="replace")
    print(f"downloading Gutenberg #{spec.gutenberg_id} to {path}")
    text = fetch_gutenberg_text(spec.gutenberg_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return text


async def _ingest(key: str, file: Path | None, embed: bool) -> None:
    spec = EDITIONS[key]
    raw = _load_edition_text(key, file)
    embedder = embedder_from_settings(get_settings()) if embed else None
    async with get_session_factory()() as session:
        report = await ingest_text(session, spec, raw, embedder)
    await dispose_engine()
    print(
        f"{spec.title}: parsed {report.parsed}, inserted {report.inserted}, "
        f"updated {report.updated}, embedded {report.embedded}"
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(prog="rizalai")
    sub = parser.add_subparsers(dest="command", required=True)

    seed = sub.add_parser("seed", help="seed units, lessons, exercises from content YAML")
    seed.add_argument("--content-dir", type=Path, default=None)

    export = sub.add_parser("export-contracts", help="write the JSON Schema for the web app")
    export.add_argument("path", type=Path, nargs="?", default=Path("../../packages/contracts/schema.json"))

    ingest = sub.add_parser("ingest", help="parse a Gutenberg edition into source_passages")
    ingest.add_argument("edition", choices=sorted(EDITIONS))
    ingest.add_argument("--file", type=Path, default=None, help="local text file; downloaded if absent")
    ingest.add_argument("--no-embed", action="store_true", help="skip the embedding step")

    args = parser.parse_args()
    if args.command == "seed":
        asyncio.run(_seed(args.content_dir or get_settings().content_dir))
    elif args.command == "export-contracts":
        export_schema(args.path)
        print(f"wrote {args.path}")
    elif args.command == "ingest":
        asyncio.run(_ingest(args.edition, args.file, embed=not args.no_embed))
