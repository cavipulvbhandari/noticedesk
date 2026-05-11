"""LLM factory keyed off ``LLM_PROVIDER_PRIMARY`` / ``LLM_PROVIDER_SECONDARY``."""

from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache

from app.core.config import get_settings
from app.services.llm.anthropic import AnthropicProvider
from app.services.llm.base import LLMError, LLMProvider
from app.services.llm.openai import OpenAIProvider
from app.services.llm.stub import StubLLMProvider
from app.services.llm.stub_canned import lookup_canned_response

KNOWN_LLM_PROVIDERS: frozenset[str] = frozenset({"anthropic", "openai", "stub"})


def _build_anthropic() -> LLMProvider:
    s = get_settings()
    if not s.anthropic_api_key:
        raise LLMError("ANTHROPIC_API_KEY must be set for anthropic provider")
    return AnthropicProvider(
        api_key=s.anthropic_api_key,
        model=s.anthropic_model,
    )


def _build_openai() -> LLMProvider:
    s = get_settings()
    if not s.openai_api_key:
        raise LLMError("OPENAI_API_KEY must be set for openai provider")
    return OpenAIProvider(
        api_key=s.openai_api_key,
        model=s.openai_model,
    )


def _build_stub() -> LLMProvider:
    def _factory(system: str, user: str) -> str:
        canned = lookup_canned_response(user)
        return canned if canned is not None else "{}"

    return StubLLMProvider(response_factory=_factory)


_BUILDERS: dict[str, Callable[[], LLMProvider]] = {
    "anthropic": _build_anthropic,
    "openai": _build_openai,
    "stub": _build_stub,
}


@lru_cache(maxsize=4)
def get_llm_provider(name: str) -> LLMProvider:
    if name not in _BUILDERS:
        raise LLMError(f"unknown LLM provider: {name!r} (valid: {sorted(_BUILDERS)})")
    return _BUILDERS[name]()


def get_primary_llm() -> LLMProvider:
    return get_llm_provider(get_settings().llm_provider_primary)


def get_secondary_llm() -> LLMProvider | None:
    name = get_settings().llm_provider_secondary
    if not name or name == get_settings().llm_provider_primary:
        return None
    return get_llm_provider(name)
