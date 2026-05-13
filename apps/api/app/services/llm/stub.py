"""Deterministic LLM stub for tests and local dev.

When invoked, returns a fixed JSON response unless the caller installed a
``response_factory`` that produces something different from the user prompt
(useful for parametrising parser evals without needing a real LLM key).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from app.services.llm.base import LLMError, LLMProvider, LLMResponse

ResponseFactory = Callable[[str, str], str]  # (system, user) -> assistant text


class StubLLMProvider(LLMProvider):
    name = "stub"

    def __init__(
        self,
        *,
        model: str = "stub-1",
        response_factory: ResponseFactory | None = None,
        canned_json: dict[str, Any] | None = None,
        fail_with: str | None = None,
    ) -> None:
        self.model = model
        self._factory = response_factory
        self._canned = canned_json
        self._fail_with = fail_with

    async def generate_text(
        self,
        *,
        system: str,
        user: str,
        max_output_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> LLMResponse:
        if self._fail_with is not None:
            raise LLMError(self._fail_with)
        if self._factory is not None:
            content = self._factory(system, user)
        elif self._canned is not None:
            content = json.dumps(self._canned)
        else:
            content = "{}"
        return LLMResponse(
            content=content,
            model=self.model,
            provider_name=self.name,
            input_tokens=len(system + user) // 4,
            output_tokens=len(content) // 4,
        )
