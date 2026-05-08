"""Confirm the dev auth bypass refuses to operate outside development."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.core.auth import AuthVerifier
from app.core.config import Settings
from app.core.errors import AuthError


def _request(headers: dict[str, str]) -> MagicMock:
    req = MagicMock()
    req.headers = headers
    return req


@pytest.mark.asyncio
async def test_dev_bypass_works_in_development() -> None:
    settings = Settings(environment="development", auth_provider="dev")
    verifier = AuthVerifier(settings=settings)
    claims = await verifier.verify(
        _request({"x-dev-user-id": "u1", "x-dev-tenant-id": "t1"})
    )
    assert claims.user_id == "u1"
    assert claims.tenant_id == "t1"


@pytest.mark.asyncio
async def test_dev_bypass_rejected_in_production() -> None:
    settings = Settings(environment="production", auth_provider="dev")
    verifier = AuthVerifier(settings=settings)
    with pytest.raises(AuthError):
        await verifier.verify(
            _request({"x-dev-user-id": "u1", "x-dev-tenant-id": "t1"})
        )


@pytest.mark.asyncio
async def test_dev_bypass_requires_headers() -> None:
    settings = Settings(environment="development", auth_provider="dev")
    verifier = AuthVerifier(settings=settings)
    with pytest.raises(AuthError):
        await verifier.verify(_request({}))
