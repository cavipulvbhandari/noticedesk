"""Idempotency + atomicity tests for the anomaly-recovery endpoints.

Sprint 3 had a latent bug: when a partner double-clicked Add Client, the
first call committed the client row before the (failing) re-route step,
and the retry hit the UNIQUE(tenant_id, pan) constraint. These tests
prove that both endpoints are now safe to call twice.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

if not os.environ.get("TEST_DATABASE_URL"):
    pytest.skip("TEST_DATABASE_URL not set", allow_module_level=True)


@pytest.fixture(autouse=True)
def _env(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("LOCAL_STORAGE_DIR", str(tmp_path))
    monkeypatch.setenv("LLM_PROVIDER_PRIMARY", "stub")
    monkeypatch.setenv("WORKFLOW_BACKEND", "inline")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("AUTH_PROVIDER", "dev")


async def _seed() -> tuple[uuid.UUID, uuid.UUID]:
    from app.core.db import session_local

    suffix = uuid.uuid4().hex[:8]
    async with session_local()() as session:
        tenant = (
            await session.execute(
                text("INSERT INTO tenants (legal_name) VALUES (:n) RETURNING tenant_id"),
                {"n": f"Idempotency Firm {suffix}"},
            )
        ).scalar_one()
        user = (
            await session.execute(
                text(
                    "INSERT INTO users (tenant_id, name, role, email) "
                    "VALUES (:t, 'P', 'partner', :e) RETURNING user_id"
                ),
                {"t": tenant, "e": f"p-{suffix}@example.com"},
            )
        ).scalar_one()
        await session.commit()
        return uuid.UUID(str(tenant)), uuid.UUID(str(user))


def _auth_headers(tenant_id, user_id) -> dict[str, str]:
    return {
        "X-Dev-User-Id": str(user_id),
        "X-Dev-Tenant-Id": str(tenant_id),
        "Content-Type": "application/json",
    }


@pytest.mark.asyncio
async def test_add_client_is_idempotent_on_pan() -> None:
    from app.main import app

    tenant_id, user_id = await _seed()
    body = {"pan": "AAACA9876B", "legal_name": "Acme Test Pvt Ltd"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r1 = await client.post("/v1/clients", headers=_auth_headers(tenant_id, user_id), json=body)
        r2 = await client.post("/v1/clients", headers=_auth_headers(tenant_id, user_id), json=body)

    assert r1.status_code == 201, r1.text
    assert r1.json()["created"] is True
    cid1 = r1.json()["client_id"]

    assert r2.status_code == 201, r2.text  # still 201; created=False signals idempotency
    assert r2.json()["created"] is False
    assert r2.json()["client_id"] == cid1


@pytest.mark.asyncio
async def test_add_registration_is_idempotent_on_identifier() -> None:
    from app.main import app

    tenant_id, user_id = await _seed()
    # First create a client.
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        rc = await client.post(
            "/v1/clients",
            headers=_auth_headers(tenant_id, user_id),
            json={"pan": "AAACA9876B", "legal_name": "Acme"},
        )
        assert rc.status_code == 201, rc.text
        cid = rc.json()["client_id"]

        body = {
            "client_id": cid,
            "registration_type": "GST",
            "identifier_value": "27AAACA9876B1Z5",
            "state_code": "27",
            "state_name": "Maharashtra",
        }
        r1 = await client.post(
            f"/v1/clients/{cid}/registrations",
            headers=_auth_headers(tenant_id, user_id),
            json=body,
        )
        r2 = await client.post(
            f"/v1/clients/{cid}/registrations",
            headers=_auth_headers(tenant_id, user_id),
            json=body,
        )

    assert r1.status_code == 201, r1.text
    assert r1.json()["created"] is True
    rid1 = r1.json()["registration_id"]

    assert r2.status_code == 201, r2.text
    assert r2.json()["created"] is False
    assert r2.json()["registration_id"] == rid1
