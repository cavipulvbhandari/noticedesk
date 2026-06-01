"""OpenAI provider (secondary LLM)."""

from __future__ import annotations

import asyncio
from typing import Any

from app.services.llm.base import (
    LLMError,
    LLMProvider,
    LLMResponse,
    LLMTransientError,
)


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "gpt-4o",
        client: Any | None = None,
        timeout_seconds: float = 180.0,
        # When set, points the SDK at any OpenAI-compatible endpoint —
        # Groq, Cerebras, Together, Fireworks, OpenRouter, Ollama, etc.
        # Leave None to talk to api.openai.com.
        base_url: str | None = None,
    ) -> None:
        self._api_key = api_key
        self.model = model
        self._client = client
        self._timeout = timeout_seconds
        self._base_url = base_url

    def _ensure_client(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            from openai import AsyncOpenAI  # type: ignore[import-not-found]
        except ImportError as e:
            raise LLMError(
                "openai SDK not installed; install it or pick a different provider"
            ) from e
        kwargs: dict[str, Any] = {"api_key": self._api_key}
        if self._base_url:
            kwargs["base_url"] = self._base_url
        self._client = AsyncOpenAI(**kwargs)
        return self._client

    async def generate_text(
        self,
        *,
        system: str,
        user: str,
        max_output_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> LLMResponse:
        client = self._ensure_client()

        async def _call() -> LLMResponse:
            try:
                resp = await client.chat.completions.create(
                    model=self.model,
                    temperature=temperature,
                    max_tokens=max_output_tokens,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                )
            except Exception as e:  # noqa: BLE001
                raise LLMTransientError(f"openai call failed: {e}") from e

            content = resp.choices[0].message.content or ""
            usage = getattr(resp, "usage", None)
            return LLMResponse(
                content=content,
                model=self.model,
                provider_name=self.name,
                input_tokens=getattr(usage, "prompt_tokens", None) if usage else None,
                output_tokens=getattr(usage, "completion_tokens", None) if usage else None,
                raw={"id": getattr(resp, "id", None)},
            )

        try:
            return await asyncio.wait_for(_call(), timeout=self._timeout)
        except TimeoutError as e:
            raise LLMTransientError(f"openai timed out after {self._timeout}s") from e
