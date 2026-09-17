"""Behaviors:
- The fake embedder is deterministic, returns bge-m3 sized dense vectors,
  and returns a sparse weight map, so ingest and tests need no network.
- The DeepInfra adapter posts the documented request shape for BAAI/bge-m3
  and parses dense vectors from the response. Sparse weights are not
  available from that endpoint, so it returns None for sparse.
- The factory picks the adapter from settings.
"""

import json

import httpx
import pytest

from rizalai.corpus.embeddings import (
    DeepInfraEmbedder,
    Embedding,
    FakeEmbedder,
    embedder_from_settings,
)
from rizalai.db.models import EMBEDDING_DIMS


def test_fake_embedder_is_deterministic_and_sized():
    fake = FakeEmbedder()
    a = fake.embed(["Dumating ang isang binata.", "Marami ang bisita."])
    b = fake.embed(["Dumating ang isang binata.", "Marami ang bisita."])
    assert a == b
    assert len(a) == 2
    assert all(len(e.dense) == EMBEDDING_DIMS for e in a)
    assert a[0].sparse is not None and "dumating" in a[0].sparse
    assert a[0].model == "fake"
    assert a[0].dense != a[1].dense


def test_deepinfra_request_shape_and_parsing():
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers.get("authorization")
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"embeddings": [[0.1] * EMBEDDING_DIMS, [0.2] * EMBEDDING_DIMS]})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    embedder = DeepInfraEmbedder(api_key="k", model="BAAI/bge-m3", client=client)
    out = embedder.embed(["uno", "dos"])

    assert seen["url"] == "https://api.deepinfra.com/v1/inference/BAAI/bge-m3"
    assert seen["auth"] == "Bearer k"
    assert seen["body"] == {"inputs": ["uno", "dos"], "normalize": True}
    assert [e.dense[0] for e in out] == [0.1, 0.2]
    assert all(e.sparse is None for e in out)
    assert out[0].model == "BAAI/bge-m3"


def test_deepinfra_rejects_wrong_dimension():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"embeddings": [[0.1] * 8]})

    embedder = DeepInfraEmbedder(api_key="k", client=httpx.Client(transport=httpx.MockTransport(handler)))
    with pytest.raises(ValueError, match="dimension"):
        embedder.embed(["x"])


def test_factory_reads_settings(monkeypatch):
    monkeypatch.setenv("EMBEDDINGS_PROVIDER", "fake")
    from rizalai.config import Settings

    assert isinstance(embedder_from_settings(Settings()), FakeEmbedder)
    monkeypatch.setenv("EMBEDDINGS_PROVIDER", "deepinfra")
    monkeypatch.setenv("EMBEDDINGS_API_KEY", "k")
    assert isinstance(embedder_from_settings(Settings()), DeepInfraEmbedder)
    monkeypatch.setenv("EMBEDDINGS_API_KEY", "")
    with pytest.raises(ValueError, match="EMBEDDINGS_API_KEY"):
        embedder_from_settings(Settings())


def test_embedding_dataclass_shape():
    e = Embedding(dense=[0.0] * EMBEDDING_DIMS, sparse={"a": 1.0}, model="fake")
    assert e.sparse == {"a": 1.0}
