from __future__ import annotations

import pytest

from app.services.llm.stub import StubLLMProvider
from app.services.llm.base import LLMError


@pytest.mark.asyncio
async def test_stub_returns_canned_json():
    provider = StubLLMProvider(canned_json={"hello": "world"})
    payload = await provider.generate_json(system="s", user="u")
    assert payload == {"hello": "world"}


@pytest.mark.asyncio
async def test_stub_can_fail():
    provider = StubLLMProvider(fail_with="boom")
    with pytest.raises(LLMError):
        await provider.generate_text(system="s", user="u")


@pytest.mark.asyncio
async def test_stub_response_factory_runs():
    provider = StubLLMProvider(
        response_factory=lambda system, user: f'{{"len": {len(user)}}}'
    )
    payload = await provider.generate_json(system="s", user="hello world")
    assert payload == {"len": 11}
