"""Integration tests for POST /v1/documents/upload + GET /v1/documents/inbox.

Skipped unless TEST_DATABASE_URL is set (so unit-only runs stay fast).
"""

from __future__ import annotations

import hashlib
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
    monkeypatch.setenv("OCR_PROVIDER_PRIMARY", "stub")
    monkeypatch.setenv("OCR_PROVIDER_FALLBACK", "")
    monkeypatch.setenv("WORKFLOW_BACKEND", "inline")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("AUTH_PROVIDER", "dev")

    from app.core.config import get_settings
    from app.services.ocr.factory import get_ocr_provider
    from app.services.storage.factory import get_storage
    from app.workflows.dispatcher import get_dispatcher

    get_settings.cache_clear()
    get_storage.cache_clear()
    get_ocr_provider.cache_clear()
    get_dispatcher.cache_clear()


async def _seed() -> tuple[uuid.UUID, uuid.UUID]:
    from app.core.db import _SessionLocal

    async with _SessionLocal() as session:
        tenant = (
            await session.execute(
                text("INSERT INTO tenants (legal_name) VALUES ('Upload Firm') RETURNING tenant_id")
            )
        ).scalar_one()
        user = (
            await session.execute(
                text(
                    "INSERT INTO users (tenant_id, name, role, email) "
                    "VALUES (:t, 'Tester', 'staff', 'tester@example.com') RETURNING user_id"
                ),
                {"t": tenant},
            )
        ).scalar_one()
        await session.commit()
        return uuid.UUID(str(tenant)), uuid.UUID(str(user))


@pytest.mark.asyncio
async def test_upload_creates_inbox_row_and_runs_ocr() -> None:
    from app.main import app

    tenant_id, user_id = await _seed()
    payload = b"%PDF-1.4 stub bytes" + (b"\n" * 1000)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/v1/documents/upload",
            headers={
                "X-Dev-User-Id": str(user_id),
                "X-Dev-Tenant-Id": str(tenant_id),
            },
            files={"file": ("notice.pdf", payload, "application/pdf")},
        )

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["file_size_bytes"] == len(payload)
    assert body["file_hash"] == hashlib.sha256(payload).hexdigest()
    assert body["ocr_status"] == "pending"

    # Wait for the inline workflow to drain.
    import asyncio

    for _ in range(40):
        await asyncio.sleep(0.05)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get(
                "/v1/documents/inbox",
                headers={
                    "X-Dev-User-Id": str(user_id),
                    "X-Dev-Tenant-Id": str(tenant_id),
                },
            )
        assert r.status_code == 200
        items = r.json()["items"]
        if items and items[0]["ocr_status"] == "completed":
            break
    else:
        pytest.fail("OCR did not complete within timeout")

    assert items[0]["ocr_provider_used"] == "stub"
    assert items[0]["ingest_channel"] == "web_upload"


@pytest.mark.asyncio
async def test_rejects_unsupported_mime() -> None:
    from app.main import app

    tenant_id, user_id = await _seed()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/v1/documents/upload",
            headers={
                "X-Dev-User-Id": str(user_id),
                "X-Dev-Tenant-Id": str(tenant_id),
            },
            files={"file": ("notice.exe", b"MZ" + b"\0" * 100, "application/x-msdownload")},
        )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "validation_error"


@pytest.mark.asyncio
async def test_rejects_oversize(monkeypatch) -> None:
    from app.main import app

    monkeypatch.setenv("MAX_UPLOAD_BYTES", "1024")
    from app.core.config import get_settings

    get_settings.cache_clear()

    tenant_id, user_id = await _seed()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/v1/documents/upload",
            headers={
                "X-Dev-User-Id": str(user_id),
                "X-Dev-Tenant-Id": str(tenant_id),
            },
            files={"file": ("big.pdf", b"x" * 4096, "application/pdf")},
        )
    assert resp.status_code == 413
