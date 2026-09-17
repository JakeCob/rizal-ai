"""Blind reflection eval across models (DECISIONS.md D09, D32).

Every model gets the same prompt. Samples are written as markdown with
random ids; the model name lives only in key.json. The owner grades on a
phone against evals/reflection/rubric.md, fills scores.csv, and summarize
joins the two.
"""

import csv
import json
import random
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from rizalai.generation.llm import LLMClient, LLMError
from rizalai.generation.prompt import build_reflection_prompt
from rizalai.generation.schema import PassageForPrompt, ReflectionDraft
from rizalai.generation.validator import validate_citations

CRITERIA = ["c1", "c2", "c3", "c4", "c5"]
HARD_FAIL_CRITERIA = {"c1", "c2"}


@dataclass
class EvalSample:
    sample_id: str
    model: str
    valid: bool
    errors: list[str]
    seconds: float
    tl: str | None
    en: str | None
    quoted_spans: list[dict[str, str]]


def _sample_markdown(sample: EvalSample, pinned: list[PassageForPrompt]) -> str:
    lines = [f"# Sample {sample.sample_id}", ""]
    if not sample.valid:
        lines += ["**Generation failed validation.**", "", *[f"- {e}" for e in sample.errors], ""]
    if sample.tl:
        lines += ["## Tagalog", "", sample.tl, "", "## English", "", sample.en or "", ""]
    if sample.quoted_spans:
        lines += ["## Quoted spans", ""]
        lines += [f'- "{s["text"]}" (passage {s["passage_id"][:8]})' for s in sample.quoted_spans]
        lines.append("")
    lines += ["## Citable passages", ""]
    lines += [f"- ({p.language}, ch {p.chapter} p {p.paragraph_index}) {p.text}" for p in pinned]
    lines.append("")
    return "\n".join(lines)


async def run_eval(
    clients: list[LLMClient],
    *,
    lesson_title: str,
    vignette_en: str,
    pinned: list[PassageForPrompt],
    style: list[PassageForPrompt],
    out_dir: Path,
    seed: int | None = None,
) -> list[EvalSample]:
    system, user = build_reflection_prompt(
        lesson_title=lesson_title, vignette_en=vignette_en, pinned=pinned, style=style
    )
    texts = {p.id: p.text for p in pinned}
    rng = random.Random(seed)  # noqa: S311 - sample ids only need to be unguessable to the grader, not secure
    samples: list[EvalSample] = []
    for client in clients:
        sample_id = f"{rng.randrange(16**6):06x}"
        started = time.perf_counter()
        errors: list[str] = []
        draft: ReflectionDraft | None = None
        try:
            draft = await client.generate(system, user, ReflectionDraft)
            errors = validate_citations(draft, texts)
        except LLMError as exc:
            errors = [str(exc)]
        samples.append(
            EvalSample(
                sample_id=sample_id,
                model=client.model,
                valid=not errors,
                errors=errors,
                seconds=round(time.perf_counter() - started, 3),
                tl=draft.tl if draft else None,
                en=draft.en if draft else None,
                quoted_spans=[{"text": s.text, "passage_id": str(s.passage_id)} for s in draft.quoted_spans]
                if draft
                else [],
            )
        )

    samples_dir = out_dir / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)
    for sample in samples:
        (samples_dir / f"{sample.sample_id}.md").write_text(
            _sample_markdown(sample, pinned), encoding="utf-8"
        )
    key = {s.sample_id: {k: v for k, v in asdict(s).items() if k != "sample_id"} for s in samples}
    (out_dir / "key.json").write_text(json.dumps(key, indent=2, ensure_ascii=False), encoding="utf-8")
    with (out_dir / "scores.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["sample_id", *CRITERIA, "notes"])
        for sample in sorted(samples, key=lambda s: s.sample_id):
            writer.writerow([sample.sample_id, "", "", "", "", "", ""])
    return samples


def summarize(out_dir: Path) -> dict[str, dict[str, Any]]:
    key = json.loads((out_dir / "key.json").read_text(encoding="utf-8"))
    summary: dict[str, dict[str, Any]] = {}
    with (out_dir / "scores.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            meta = key.get(row["sample_id"])
            if meta is None or not row.get("c1"):
                continue
            scores = {c: int(row[c]) for c in CRITERIA if row.get(c)}
            entry = summary.setdefault(
                meta["model"],
                {"samples": 0, "total": 0, "failed_hard": False, "valid": meta["valid"], "seconds": []},
            )
            entry["samples"] += 1
            entry["total"] += sum(scores.values())
            entry["failed_hard"] = entry["failed_hard"] or any(scores.get(c) == 0 for c in HARD_FAIL_CRITERIA)
            entry["seconds"].append(meta["seconds"])
    for entry in summary.values():
        entry["mean"] = round(entry["total"] / entry["samples"], 2) if entry["samples"] else 0.0
        entry["mean_seconds"] = (
            round(sum(entry["seconds"]) / len(entry["seconds"]), 2) if entry["seconds"] else 0.0
        )
        del entry["seconds"]
    return summary
