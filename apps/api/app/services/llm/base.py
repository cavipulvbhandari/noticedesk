"""LLM provider contract."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any


class LLMError(Exception):
    """Permanent LLM failure (auth, model-unavailable, etc.)."""


class LLMTransientError(LLMError):
    """Temporary failure (timeout, 5xx, throttling) — safe to retry."""


class JsonSchemaValidationError(LLMError):
    """LLM returned valid JSON but it doesn't satisfy the requested schema."""


@dataclass(frozen=True, slots=True)
class LLMResponse:
    """Output of a single LLM call."""

    content: str
    model: str
    provider_name: str
    # input / output token counts when the SDK exposes them; useful for cost
    # accounting downstream.
    input_tokens: int | None = None
    output_tokens: int | None = None
    raw: dict[str, Any] = field(default_factory=dict)


class LLMProvider(abc.ABC):
    """Async LLM provider interface.

    The contract is deliberately minimal — one synchronous-feeling
    ``generate_json`` method that always returns parsed JSON. Agents that
    need free-form text can call ``generate_text``.
    """

    name: str
    model: str

    @abc.abstractmethod
    async def generate_text(
        self,
        *,
        system: str,
        user: str,
        max_output_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> LLMResponse:
        ...

    async def generate_json(
        self,
        *,
        system: str,
        user: str,
        max_output_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        """Convenience: call :meth:`generate_text` and JSON-parse the result.

        Subclasses can override if their SDK exposes a structured-output
        mode that's strictly better than parsing free text.
        """
        import json

        response = await self.generate_text(
            system=system,
            user=user,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
        )
        # Anthropic / OpenAI sometimes wrap JSON in ```json ... ``` fences;
        # strip those before parsing.
        text = _strip_code_fence(response.content)
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise JsonSchemaValidationError(
                f"{self.name} returned non-JSON content: {e}"
            ) from e


def _strip_code_fence(text: str) -> str:
    s = text.strip()
    if not s.startswith("```"):
        return s
    # Strip leading ```[lang]\n and trailing ```
    lines = s.splitlines()
    if len(lines) < 2:
        return s
    first = lines[0].strip()
    if first.startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines)
