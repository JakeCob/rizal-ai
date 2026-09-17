"""Operator commands: seed content, export contracts.

Usage:
  uv run rizalai seed
  uv run rizalai export-contracts [path]
"""

import argparse
import asyncio
import logging
from pathlib import Path

from rizalai.config import get_settings
from rizalai.content.seed import seed_content
from rizalai.contracts.export import export_schema
from rizalai.db.session import dispose_engine, get_session_factory


async def _seed(content_dir: Path) -> None:
    async with get_session_factory()() as session:
        report = await seed_content(session, content_dir)
    await dispose_engine()
    print(
        f"seeded {report.units} units, {report.lessons} lessons, {report.exercises} exercises; "
        f"{report.unresolved_passages} passage refs unresolved"
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(prog="rizalai")
    sub = parser.add_subparsers(dest="command", required=True)

    seed = sub.add_parser("seed", help="seed units, lessons, exercises from content YAML")
    seed.add_argument("--content-dir", type=Path, default=None)

    export = sub.add_parser("export-contracts", help="write the JSON Schema for the web app")
    export.add_argument("path", type=Path, nargs="?", default=Path("../../packages/contracts/schema.json"))

    args = parser.parse_args()
    if args.command == "seed":
        content_dir = args.content_dir or get_settings().content_dir
        asyncio.run(_seed(content_dir))
    elif args.command == "export-contracts":
        export_schema(args.path)
        print(f"wrote {args.path}")
