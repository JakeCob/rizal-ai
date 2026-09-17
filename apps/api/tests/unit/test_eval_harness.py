"""Behaviors for the blind reflection eval (DECISIONS.md D09, D32):
- one sample per model per lesson, written as markdown for reading on a
  phone, with ids that do not reveal the model
- key.json maps sample ids to models and is the only place the model appears
- a scores.csv template is written with one row per sample
- summarize joins scores with the key into per-model means
- a model whose draft fails validation is recorded as failed, not skipped
"""

import csv
import json
import uuid
from pathlib import Path

import pytest

from rizalai.generation.evals import EvalSample, run_eval, summarize
from rizalai.generation.llm import FakeLLMClient
from rizalai.generation.schema import PassageForPrompt

pytestmark = pytest.mark.anyio

P_ES = PassageForPrompt(
    id=uuid.uuid4(), language="es", chapter=2, paragraph_index=3, text="Tengo el honor de presentar"
)
P_TL = PassageForPrompt(
    id=uuid.uuid4(), language="tl", chapter=2, paragraph_index=3, text="May capurihan acóng ipakilala"
)


def _fake(model: str, draft: dict) -> FakeLLMClient:
    client = FakeLLMClient()
    client.model = model
    client.queue(draft, draft)
    return client


async def test_run_eval_writes_blind_samples_and_key(tmp_path: Path):
    good = {
        "tl": "Isang gabi.",
        "en": "One night.",
        "quoted_spans": [{"text": "honor de presentar", "passage_id": str(P_ES.id)}],
    }
    bad = {"tl": "x", "en": "y", "quoted_spans": [{"text": "never said", "passage_id": str(P_ES.id)}]}
    clients = [_fake("model-a", good), _fake("model-b", bad)]

    samples = await run_eval(
        clients,
        lesson_title="Ibarra arrives",
        vignette_en="Capitan Tiago presents Ibarra.",
        pinned=[P_ES, P_TL],
        style=[],
        out_dir=tmp_path,
        seed=7,
    )
    assert len(samples) == 2
    assert all(isinstance(s, EvalSample) for s in samples)
    ok = next(s for s in samples if s.model == "model-a")
    failed = next(s for s in samples if s.model == "model-b")
    assert ok.valid is True and failed.valid is False
    assert "model" not in ok.sample_id and "model" not in failed.sample_id

    key = json.loads((tmp_path / "key.json").read_text())
    assert key[ok.sample_id]["model"] == "model-a"
    assert key[failed.sample_id]["model"] == "model-b"

    text = (tmp_path / "samples" / f"{ok.sample_id}.md").read_text()
    assert "Isang gabi." in text and "One night." in text and "model-a" not in text
    with (tmp_path / "scores.csv").open() as fh:
        rows = list(csv.DictReader(fh))
    assert {r["sample_id"] for r in rows} == {ok.sample_id, failed.sample_id}
    assert set(rows[0]) == {"sample_id", "c1", "c2", "c3", "c4", "c5", "notes"}


async def test_summarize_joins_scores_with_key(tmp_path: Path):
    good = {"tl": "Isang gabi.", "en": "One night.", "quoted_spans": []}
    samples = await run_eval(
        [_fake("model-a", good), _fake("model-b", good)],
        lesson_title="t",
        vignette_en="v",
        pinned=[P_ES],
        style=[],
        out_dir=tmp_path,
        seed=1,
    )
    by_model = {s.model: s.sample_id for s in samples}
    with (tmp_path / "scores.csv").open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["sample_id", "c1", "c2", "c3", "c4", "c5", "notes"])
        writer.writerow([by_model["model-a"], 2, 2, 2, 1, 2, ""])
        writer.writerow([by_model["model-b"], 1, 0, 1, 1, 1, "invents a letter"])
    summary = summarize(tmp_path)
    assert summary["model-a"]["total"] == 9
    assert summary["model-b"]["total"] == 4
    assert summary["model-b"]["failed_hard"] is True  # a 0 on criterion 2
    assert summary["model-a"]["failed_hard"] is False
