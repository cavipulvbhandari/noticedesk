"""Per-agent LLM model routing.

The cost-tier split (Opus for drafting, Sonnet for parsing + triage) is
configured via three env-driven fields on Settings. These tests pin the
fall-through logic so an accidental refactor doesn't silently route every
agent at Opus prices.
"""

from __future__ import annotations

import pytest

from app.core.config import Settings
from app.services.llm import factory as llm_factory


def _build_settings(**overrides) -> Settings:
    defaults = {
        "llm_provider_primary": "anthropic",
        "anthropic_api_key": "sk-test",
        "anthropic_model": "claude-opus-4-7",
        "llm_model_drafting": "",
        "llm_model_triage": "claude-sonnet-4-6",
        "llm_model_parsing": "claude-sonnet-4-6",
    }
    defaults.update(overrides)
    return Settings(**defaults)


def test_drafting_falls_through_to_anthropic_model_when_unset() -> None:
    s = _build_settings(llm_model_drafting="")
    assert s.model_for_agent("drafting", provider="anthropic") == "claude-opus-4-7"


def test_drafting_honours_explicit_override() -> None:
    s = _build_settings(llm_model_drafting="claude-opus-4-8")
    assert s.model_for_agent("drafting", provider="anthropic") == "claude-opus-4-8"


def test_triage_defaults_to_sonnet() -> None:
    s = _build_settings()
    assert s.model_for_agent("triage", provider="anthropic") == "claude-sonnet-4-6"


def test_parsing_defaults_to_sonnet() -> None:
    s = _build_settings()
    assert s.model_for_agent("parsing", provider="anthropic") == "claude-sonnet-4-6"


def test_openai_provider_ignores_anthropic_overrides() -> None:
    """Pointing LLM_MODEL_TRIAGE at a Claude name shouldn't break an
    OpenAI deployment — provider-mismatched overrides are dropped."""
    s = _build_settings(openai_model="gpt-4o")
    assert s.model_for_agent("triage", provider="openai") == "gpt-4o"


def test_factory_routes_each_agent_to_its_model(monkeypatch) -> None:
    """End-to-end: the factory builds a provider whose ``model`` attribute
    matches what the agent requested. Drafting → Opus, triage → Sonnet."""
    settings = _build_settings()
    monkeypatch.setattr(llm_factory, "get_settings", lambda: settings)
    # Anthropic provider builds lazily without making any network call, so
    # we can introspect .model directly without needing the real SDK.
    drafting_llm = llm_factory.get_llm_for_agent("drafting")
    triage_llm = llm_factory.get_llm_for_agent("triage")
    parsing_llm = llm_factory.get_llm_for_agent("parsing")
    assert drafting_llm.model == "claude-opus-4-7"
    assert triage_llm.model == "claude-sonnet-4-6"
    assert parsing_llm.model == "claude-sonnet-4-6"
    # Provider instances are cached per (name, model) so different agents
    # sharing a model share an instance — important for SDK client reuse.
    assert triage_llm is parsing_llm
    assert drafting_llm is not triage_llm
