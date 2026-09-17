"""LLM clients behind one protocol (DECISIONS.md D09, D32).

FakeLLMClient serves queued drafts and records calls; tests and keyless
local runs use it. OpenRouterLLMClient is the production path: OpenAI
compatible chat completions with a strict JSON schema response, any model
by id. AnthropicLLMClient calls the direct API with structured output and
stays available as an alternative. Provider and model are config.
"""

import json
import re
from collections import deque
from functools import lru_cache
from typing import Any, Protocol, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from rizalai.config import Settings, get_settings

T = TypeVar("T", bound=BaseModel)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_DEFAULT_MODEL = "anthropic/claude-opus-5"
ANTHROPIC_DEFAULT_MODEL = "claude-opus-5"
APP_URL = "https://github.com/JakeCob/rizal-ai"
APP_TITLE = "RizalAI"

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


class LLMError(Exception):
    """The model could not produce a usable structured response."""


class LLMClient(Protocol):
    model: str

    async def generate(self, system: str, user: str, schema: type[T]) -> T: ...


class FakeLLMClient:
    model = "fake"

    def __init__(self) -> None:
        self._queue: deque[dict[str, Any]] = deque()
        self.calls = 0
        self.last_system_prompt = ""
        self.last_user_prompt = ""

    def queue(self, *drafts: dict[str, Any]) -> None:
        self._queue.extend(drafts)

    async def generate(self, system: str, user: str, schema: type[T]) -> T:
        self.calls += 1
        self.last_system_prompt = system
        self.last_user_prompt = user
        if not self._queue:
            raise LLMError("FakeLLMClient has no queued draft")
        return schema.model_validate(self._queue.popleft())


def strict_json_schema(schema: type[BaseModel]) -> dict[str, Any]:
    """Pydantic's schema with additionalProperties: false on every object,
    which OpenAI-style strict mode requires."""

    def close(node: Any) -> Any:
        if isinstance(node, dict):
            if node.get("type") == "object" and "additionalProperties" not in node:
                node["additionalProperties"] = False
            return {k: close(v) for k, v in node.items()}
        if isinstance(node, list):
            return [close(v) for v in node]
        return node

    result: dict[str, Any] = close(schema.model_json_schema())
    return result


class OpenRouterLLMClient:
    def __init__(
        self,
        api_key: str,
        model: str = OPENROUTER_DEFAULT_MODEL,
        max_tokens: int = 4096,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.model = model
        self._max_tokens = max_tokens
        self._client = client or httpx.AsyncClient(timeout=120.0)
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": APP_URL,
            "X-Title": APP_TITLE,
            "Content-Type": "application/json",
        }

    async def generate(self, system: str, user: str, schema: type[T]) -> T:
        body = {
            "model": self.model,
            "max_tokens": self._max_tokens,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema.__name__,
                    "strict": True,
                    "schema": strict_json_schema(schema),
                },
            },
        }
        try:
            response = await self._client.post(OPENROUTER_URL, headers=self._headers, json=body)
        except httpx.HTTPError as exc:
            raise LLMError(f"openrouter request failed: {exc}") from exc
        if response.status_code != 200:
            raise LLMError(f"openrouter returned {response.status_code}: {response.text[:200]}")

        try:
            choice = response.json()["choices"][0]
        except (KeyError, IndexError, ValueError) as exc:
            raise LLMError("openrouter response had no choices") from exc
        if choice.get("finish_reason") == "content_filter":
            raise LLMError("model refused the request")
        message = choice.get("message") or {}
        content = message.get("content")
        if not content:
            raise LLMError(f"model returned no content: {message.get('refusal') or 'empty'}")

        text = _FENCE.sub("", content.strip())
        try:
            return schema.model_validate(json.loads(text))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise LLMError(f"model output did not match {schema.__name__}: {exc}") from exc


class AnthropicLLMClient:
    """Claude via the official SDK. Structured output through messages.parse
    keeps the response schema-valid; a refusal stop reason is surfaced as
    LLMError so the caller can fall back."""

    def __init__(self, api_key: str, model: str = ANTHROPIC_DEFAULT_MODEL, max_tokens: int = 4096) -> None:
        from anthropic import AsyncAnthropic

        self.model = model
        self._max_tokens = max_tokens
        self._client = AsyncAnthropic(api_key=api_key)

    async def generate(self, system: str, user: str, schema: type[T]) -> T:
        response = await self._client.messages.parse(
            model=self.model,
            max_tokens=self._max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_format=schema,
        )
        if response.stop_reason == "refusal":
            raise LLMError("model refused the request")
        parsed = response.parsed_output
        if parsed is None:
            raise LLMError("model returned no structured output")
        return parsed


def build_llm_client(settings: Settings, model: str | None = None) -> LLMClient:
    chosen = model or settings.llm_model
    if settings.llm_provider == "fake":
        return FakeLLMClient()
    if settings.llm_provider == "openrouter":
        if not settings.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY is required for the openrouter provider")
        return OpenRouterLLMClient(
            api_key=settings.openrouter_api_key, model=chosen or OPENROUTER_DEFAULT_MODEL
        )
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY is required for the anthropic provider")
    return AnthropicLLMClient(api_key=settings.anthropic_api_key, model=chosen or ANTHROPIC_DEFAULT_MODEL)


@lru_cache
def _cached_client() -> LLMClient:
    return build_llm_client(get_settings())


def get_llm_client() -> LLMClient:
    """FastAPI dependency. Overridden in tests with a FakeLLMClient."""
    return _cached_client()
