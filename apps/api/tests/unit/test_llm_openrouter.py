"""Behaviors for the OpenRouter adapter (DECISIONS.md D32):
- posts an OpenAI-compatible chat completion with the bearer key, the
  attribution headers, the system and user messages, and a strict JSON
  schema response_format built from the Pydantic model
- parses choices[0].message.content into the schema
- a refusal, an empty message, invalid JSON, or an HTTP error becomes
  LLMError so the caller can fall back
- the model is a per-client setting, so the eval harness can run several
- the factory picks openrouter from settings and requires the key
"""

import json

import httpx
import pytest

from rizalai.generation.llm import (
    AnthropicLLMClient,
    FakeLLMClient,
    LLMError,
    OpenRouterLLMClient,
    build_llm_client,
)
from rizalai.generation.schema import ReflectionDraft

pytestmark = pytest.mark.anyio

GOOD = {"tl": "Isang hapunan.", "en": "A dinner.", "quoted_spans": []}


def _client(handler) -> OpenRouterLLMClient:
    transport = httpx.MockTransport(handler)
    return OpenRouterLLMClient(
        api_key="or-key",
        model="anthropic/claude-opus-5",
        client=httpx.AsyncClient(transport=transport),
    )


def _ok(content: str, finish: str = "stop") -> httpx.Response:
    return httpx.Response(
        200,
        json={"choices": [{"message": {"role": "assistant", "content": content}, "finish_reason": finish}]},
    )


async def test_request_shape_and_parsing():
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["headers"] = dict(request.headers)
        seen["body"] = json.loads(request.content)
        return _ok(json.dumps(GOOD))

    client = _client(handler)
    draft = await client.generate("SYS", "USER", ReflectionDraft)

    assert draft == ReflectionDraft.model_validate(GOOD)
    assert seen["url"] == "https://openrouter.ai/api/v1/chat/completions"
    assert seen["headers"]["authorization"] == "Bearer or-key"
    assert seen["headers"]["http-referer"].startswith("https://github.com/JakeCob/rizal-ai")
    assert seen["headers"]["x-title"] == "RizalAI"
    body = seen["body"]
    assert body["model"] == "anthropic/claude-opus-5"
    assert body["messages"] == [{"role": "system", "content": "SYS"}, {"role": "user", "content": "USER"}]
    fmt = body["response_format"]
    assert fmt["type"] == "json_schema"
    assert fmt["json_schema"]["name"] == "ReflectionDraft"
    assert fmt["json_schema"]["strict"] is True
    assert set(fmt["json_schema"]["schema"]["properties"]) == {"tl", "en", "quoted_spans"}
    assert fmt["json_schema"]["schema"]["additionalProperties"] is False
    assert body["max_tokens"] >= 1024
    assert client.model == "anthropic/claude-opus-5"


async def test_content_filter_and_empty_and_bad_json_raise():
    async def run(handler):
        with pytest.raises(LLMError):
            await _client(handler).generate("s", "u", ReflectionDraft)

    await run(lambda r: _ok(json.dumps(GOOD), finish="content_filter"))
    await run(
        lambda r: httpx.Response(200, json={"choices": [{"message": {"content": None, "refusal": "no"}}]})
    )
    await run(lambda r: _ok("not json at all"))
    await run(lambda r: _ok(json.dumps({"tl": "x"})))  # schema-invalid
    await run(lambda r: httpx.Response(429, json={"error": {"message": "rate limited"}}))
    await run(lambda r: httpx.Response(200, json={"choices": []}))


async def test_strips_code_fences_some_models_add():
    client = _client(lambda r: _ok("```json\n" + json.dumps(GOOD) + "\n```"))
    draft = await client.generate("s", "u", ReflectionDraft)
    assert draft.tl == "Isang hapunan."


def test_factory_picks_provider(monkeypatch):
    from rizalai.config import Settings

    monkeypatch.setenv("LLM_PROVIDER", "fake")
    assert isinstance(build_llm_client(Settings()), FakeLLMClient)

    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        build_llm_client(Settings())
    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    client = build_llm_client(Settings())
    assert isinstance(client, OpenRouterLLMClient)
    assert client.model == "anthropic/claude-opus-5"  # default for openrouter

    monkeypatch.setenv("LLM_MODEL", "qwen/qwen3.8-max-0902")
    assert build_llm_client(Settings()).model == "qwen/qwen3.8-max-0902"

    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("LLM_MODEL", "")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    direct = build_llm_client(Settings())
    assert isinstance(direct, AnthropicLLMClient)
    assert direct.model == "claude-opus-5"  # default for the direct SDK
