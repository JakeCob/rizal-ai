"""Embeddings behind a protocol (DECISIONS.md D10).

FakeEmbedder: deterministic, no network, used by tests and by local runs
without a key. DeepInfraEmbedder: hosted bge-m3 dense vectors. The hosted
endpoint does not expose bge-m3 lexical weights, so sparse is None there;
see docs/tech-debt.md item 8.
"""

import hashlib
import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Protocol

import httpx

from rizalai.config import Settings
from rizalai.db.models import EMBEDDING_DIMS

DEEPINFRA_URL = "https://api.deepinfra.com/v1/inference/{model}"


@dataclass(frozen=True)
class Embedding:
    dense: list[float]
    sparse: dict[str, float] | None
    model: str


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[Embedding]: ...


_TOKEN = re.compile(r"[\wáéíóúñü~]+", re.IGNORECASE)


class FakeEmbedder:
    """Hash-seeded unit vectors plus term-frequency sparse weights."""

    model = "fake"

    def embed(self, texts: list[str]) -> list[Embedding]:
        return [Embedding(dense=self._dense(t), sparse=self._sparse(t), model=self.model) for t in texts]

    @staticmethod
    def _dense(text: str) -> list[float]:
        out: list[float] = []
        counter = 0
        while len(out) < EMBEDDING_DIMS:
            digest = hashlib.sha256(f"{counter}:{text}".encode()).digest()
            out.extend((b - 127.5) / 127.5 for b in digest)
            counter += 1
        vec = out[:EMBEDDING_DIMS]
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    @staticmethod
    def _sparse(text: str) -> dict[str, float]:
        counts = Counter(t.lower() for t in _TOKEN.findall(text))
        total = sum(counts.values()) or 1
        return {tok: round(n / total, 6) for tok, n in counts.items()}


class DeepInfraEmbedder:
    def __init__(self, api_key: str, model: str = "BAAI/bge-m3", client: httpx.Client | None = None) -> None:
        self.model = model
        self._client = client or httpx.Client(timeout=60.0)
        self._headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    def embed(self, texts: list[str]) -> list[Embedding]:
        response = self._client.post(
            DEEPINFRA_URL.format(model=self.model),
            headers=self._headers,
            json={"inputs": texts, "normalize": True},
        )
        response.raise_for_status()
        vectors = response.json()["embeddings"]
        out: list[Embedding] = []
        for vec in vectors:
            if len(vec) != EMBEDDING_DIMS:
                raise ValueError(f"unexpected embedding dimension {len(vec)}, expected {EMBEDDING_DIMS}")
            out.append(Embedding(dense=[float(v) for v in vec], sparse=None, model=self.model))
        return out


def embedder_from_settings(settings: Settings) -> Embedder:
    if settings.embeddings_provider == "fake":
        return FakeEmbedder()
    if not settings.embeddings_api_key:
        raise ValueError("EMBEDDINGS_API_KEY is required for the deepinfra provider")
    return DeepInfraEmbedder(api_key=settings.embeddings_api_key, model=settings.embeddings_model)
