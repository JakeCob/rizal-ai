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

from rizalai.audio.engines import available_engines, engine_by_name
from rizalai.audio.render import bakeoff, render_lines
from rizalai.audio.routes import get_audio_store
from rizalai.audio.store import AudioStore
from rizalai.config import get_settings
from rizalai.content.seed import seed_content
from rizalai.contracts.export import export_schema
from rizalai.corpus.embeddings import embedder_from_settings
from rizalai.corpus.gutenberg import EDITIONS, fetch_gutenberg_text
from rizalai.corpus.ingest import ingest_text
from rizalai.db.session import dispose_engine, get_session_factory
from rizalai.generation.evals import run_eval, summarize
from rizalai.generation.llm import build_llm_client
from rizalai.generation.service import list_reflections, reject_reflection

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


def _store() -> AudioStore:
    return get_audio_store()


def _content_lines(content_dir: Path) -> list[str]:
    from rizalai.content.loader import load_content

    lines: list[str] = []
    for unit in load_content(content_dir):
        for lesson in unit.lessons:
            lines += [b.tl for b in lesson.vignette]
            lines += [e.transcript_tl for e in lesson.exercises if e.type == "listen_tap"]
    return lines


async def _render_audio(engine_name: str, content_dir: Path) -> None:
    settings = get_settings()
    engine = engine_by_name(engine_name, settings)
    store = _store()
    report = render_lines(_content_lines(content_dir), engine, store)
    print(f"{engine.name}: rendered {report.rendered}, skipped {report.skipped}")
    async with get_session_factory()() as session:
        seeded = await seed_content(session, content_dir, audio=(store, engine))
    await dispose_engine()
    print(f"re-seeded {seeded.lessons} lessons with audio urls")


def _bakeoff(content_dir: Path, out_dir: Path, count: int) -> None:
    settings = get_settings()
    engines = available_engines(settings)
    lines = _content_lines(content_dir)[:count]
    written = bakeoff(lines, engines, out_dir)
    print(f"engines: {[e.name for e in engines]}")
    print(f"wrote {len(written)} samples to {out_dir}; listen on a phone and pick by ear")
    for i, text in enumerate(lines, start=1):
        print(f"  {i:02d}: {text}")


async def _eval_reflection(models: list[str], lesson_slug: str, out_dir: Path) -> None:
    import json
    from datetime import UTC, datetime

    from sqlalchemy import select

    from rizalai.content.loader import lesson_id
    from rizalai.corpus.retrieval import pinned_passages, style_context
    from rizalai.db.models import Lesson, SourcePassage
    from rizalai.generation.schema import PassageForPrompt

    settings = get_settings()
    clients = [build_llm_client(settings, model=m) for m in models]
    async with get_session_factory()() as session:
        lesson = await session.scalar(select(Lesson).where(Lesson.id == lesson_id(lesson_slug)))
        if lesson is None:
            raise SystemExit(f"lesson {lesson_slug!r} is not seeded")
        pinned_rows = await pinned_passages(session, lesson.source_passage_ids)
        chapters = sorted({p.chapter for p in pinned_rows})
        style_rows = await style_context(
            session, work="noli", language="tl", chapters=chapters, exclude=[p.id for p in pinned_rows]
        )

        def to_prompt(p: SourcePassage) -> PassageForPrompt:
            return PassageForPrompt(
                id=p.id,
                language=p.language,
                chapter=p.chapter,
                paragraph_index=p.paragraph_index,
                text=p.text,
            )

        vignette_en = " ".join(str(b.get("en", "")) for b in lesson.vignette)
        target = out_dir / datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        samples = await run_eval(
            clients,
            lesson_title=lesson.title,
            vignette_en=vignette_en,
            pinned=[to_prompt(p) for p in pinned_rows],
            style=[to_prompt(p) for p in style_rows],
            out_dir=target,
        )
    await dispose_engine()
    print(f"wrote {len(samples)} samples to {target}/samples")
    print("grade them with evals/reflection/rubric.md into scores.csv, then run eval-summary")
    print(json.dumps({s.sample_id: {"valid": s.valid, "seconds": s.seconds} for s in samples}, indent=2))


async def _reflections(action: str, cache_id: str | None) -> None:
    import uuid

    async with get_session_factory()() as session:
        if action == "list":
            for row in await list_reflections(session):
                created = f"{row.created_at:%Y-%m-%d %H:%M}"
                print(
                    f"{row.id}  {row.status:<9} valid={row.citations_valid!s:<5} model={row.model} "
                    f"prompt={row.prompt_version} judge={row.judge_score} created={created}"
                )
        elif action == "reject" and cache_id:
            ok = await reject_reflection(session, uuid.UUID(cache_id))
            print("rejected" if ok else "not found")
    await dispose_engine()


def _non_negative(value: str) -> int:
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError("must be 0 or more")
    return number


def _orders(args: argparse.Namespace) -> None:
    import yaml
    from pydantic import ValidationError

    from rizalai.content.loader import load_lesson
    from rizalai.content.orders import format_report, movers_for, report
    from rizalai.contracts.lesson import ListenTap, TokenExercise

    path: Path = args.lesson
    try:
        lesson = load_lesson(path)
    except OSError as err:
        raise SystemExit(f"cannot read {path}: {err.strerror or err}") from None
    except (ValidationError, yaml.YAMLError, TypeError) as err:
        first = str(err).splitlines()[0]
        raise SystemExit(f"{path} is not a valid lesson file ({first})") from None

    exercises = list(lesson.exercises)
    if args.key is not None:
        exercises = [e for e in exercises if e.key == args.key]
        if not exercises:
            raise SystemExit(f"no exercise with key {args.key} in {path}")
        if not isinstance(exercises[0], TokenExercise):
            raise SystemExit(
                f"{args.key} is a comprehension_mc (multiple choice) exercise; it has no word order"
            )
    for ex in exercises:
        if not isinstance(ex, TokenExercise):
            continue
        if isinstance(ex, ListenTap) and args.key is None and not args.include_listen_tap:
            print(
                f"{ex.key} listen_tap: skipped, it grades the transcript as heard"
                " (--include-listen-tap to list)"
            )
            print()
            continue
        r = report(
            ex,
            movers_for(ex, args.clitics),
            args.max,
            split=args.split,
            bank=args.bank,
            phrases=args.phrases,
        )
        print(format_report(r))
        print()


def main(argv: list[str] | None = None) -> int:
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

    render = sub.add_parser(
        "render-audio", help="render vignette lines with a TTS engine and re-seed audio urls"
    )
    render.add_argument("--engine", default=None, help="fake | mms | xtts | google (default: TTS_ENGINE)")
    render.add_argument("--content-dir", type=Path, default=None)

    bake = sub.add_parser("tts-bakeoff", help="render sample lines with every available engine")
    bake.add_argument("--out", type=Path, default=Path("samples/tts"))
    bake.add_argument("--lines", type=int, default=3)
    bake.add_argument("--content-dir", type=Path, default=None)

    ev = sub.add_parser("eval-reflection", help="blind eval of the reflection across models (D09, D32)")
    ev.add_argument("--models", required=True, help="comma separated OpenRouter model ids")
    ev.add_argument("--lesson", default="noli-ibarra-arrival")
    ev.add_argument("--out", type=Path, default=Path("../../evals/reflection/results"))

    evs = sub.add_parser("eval-summary", help="join scores.csv with key.json for one eval run")
    evs.add_argument("run_dir", type=Path)

    reflections = sub.add_parser("reflections", help="list or reject cached reflections")
    reflections.add_argument("action", choices=["list", "reject"])
    reflections.add_argument("cache_id", nargs="?", default=None)

    orders = sub.add_parser("orders", help="list the word orders a token exercise's tiles can build")
    orders.add_argument("lesson", type=Path, help="a lesson YAML file")
    orders.add_argument("--key", default=None, help="one exercise, for example ex4")
    orders.add_argument("--clitics", default=None, help="comma separated movers, replacing the defaults")
    orders.add_argument("--max", type=_non_negative, default=50, help="candidates to print per exercise")
    orders.add_argument("--split", action="store_true", help="move each particle alone, not in runs")
    orders.add_argument("--bank", action="store_true", help="also drop, swap or add bank particles")
    orders.add_argument("--phrases", action="store_true", help="also move whole phrases (kay ..., sa ...)")
    orders.add_argument(
        "--include-listen-tap",
        action="store_true",
        help="also list listen_tap orders (they grade the transcript)",
    )

    args = parser.parse_args(argv)
    if args.command == "seed":
        asyncio.run(_seed(args.content_dir or get_settings().content_dir))
    elif args.command == "export-contracts":
        export_schema(args.path)
        print(f"wrote {args.path}")
    elif args.command == "ingest":
        asyncio.run(_ingest(args.edition, args.file, embed=not args.no_embed))
    elif args.command == "reflections":
        asyncio.run(_reflections(args.action, args.cache_id))
    elif args.command == "eval-reflection":
        asyncio.run(
            _eval_reflection([m.strip() for m in args.models.split(",") if m.strip()], args.lesson, args.out)
        )
    elif args.command == "eval-summary":
        import json

        print(json.dumps(summarize(args.run_dir), indent=2))
    elif args.command == "render-audio":
        asyncio.run(
            _render_audio(
                args.engine or get_settings().tts_engine, args.content_dir or get_settings().content_dir
            )
        )
    elif args.command == "tts-bakeoff":
        _bakeoff(args.content_dir or get_settings().content_dir, args.out, args.lines)
    elif args.command == "orders":
        _orders(args)
    return 0
