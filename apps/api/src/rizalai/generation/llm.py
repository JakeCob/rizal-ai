"""LLM clients behind one protocol (DECISIONS.md D09).

FakeLLMClient serves queued drafts and records calls; tests and keyless
local runs use it. AnthropicLLMClient calls Claude with structured output so
the response is a validated ReflectionDraft. Provider and model are config.
"""

import asyncio
from collections import deque
from functools import lru_cache
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

from rizalai.config import Settings, get_settings

T = TypeVar("T", bound=BaseModel)


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


class AnthropicLLMClient:
    """Claude via the official SDK. Structured output through messages.parse
    keeps the response schema-valid; a refusal stop reason is surfaced as
    LLMError so the caller can fall back."""

    def __init__(self, api_key: str, model: str = "claude-opus-5", max_tokens: int = 4096) -> None:
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


def build_llm_client(settings: Settings) -> LLMClient:
    if settings.llm_provider == "fake":
        return FakeLLMClient()
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY is required for the anthropic provider")
    return AnthropicLLMClient(api_key=settings.anthropic_api_key, model=settings.llm_model)


@lru_cache
def _cached_client() -> LLMClient:
    return build_llm_client(get_settings())


def get_llm_client() -> LLMClient:
    """FastAPI dependency. Overridden in tests with a FakeLLMClient."""
    return _cached_client()


async def run_blocking(fn: Any, *args: Any) -> Any:
    return await asyncio.to_thread(fn, *args)
