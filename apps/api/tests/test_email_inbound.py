"""Email-inbound webhook integration test."""

from __future__ import annotations

import base64
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
    monkeypatch.setenv("EMAIL_INBOUND_WEBHOOK_SECRET", "shh")
    monkeypatch.setenv("EMAIL_INBOUND_DOMAIN", "noticedesk.in")

    from app.core.config import get_settings
    from app.services.ocr.factory import get_ocr_provider
    from app.services.storage.factory import get_storage
    from app.workflows.dispatcher import get_dispatcher

    get_settings.cache_clear()
    get_storage.cache_clear()
    get_ocr_provider.cache_clear()
    get_dispatcher.cache_clear()


async def _seed_tenant_with_slug(slug: str) -> uuid.UUID:
    from app.core.db import session_local

    async with session_local()() as session:
        tid = (
            await session.execute(
                text(
                    "INSERT INTO tenants (legal_name, slug) VALUES (:n, :s) RETURNING tenant_id"
                ),
                {"n": f"Mehta & Associates {slug}", "s": slug},
            )
        ).scalar_one()
        await session.commit()
        return uuid.UUID(str(tid))


def _unique_slug(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


@pytest.mark.asyncio
async def test_email_creates_inbox_rows() -> None:
    from app.main import app

    slug = _unique_slug("mehta")
    tenant_id = await _seed_tenant_with_slug(slug)
    pdf = b"%PDF-1.4 stub" + b"\0" * 200

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/v1/email/inbound",
            headers={"X-Webhook-Secret": "shh"},
            json={
                "sender": "officer@gst.gov.in",
                "recipient": f"notices+{slug}@noticedesk.in",
                "subject": "DRC-01 Issued",
                "received_at": "2026-05-09T10:00:00Z",
                "attachments": [
                    {
                        "filename": "drc-01.pdf",
                        "mime_type": "application/pdf",
                        "content_b64": base64.b64encode(pdf).decode(),
                    },
                    {
                        "filename": "should-skip.exe",
                        "mime_type": "application/x-msdownload",
                        "content_b64": base64.b64encode(b"x").decode(),
                    },
                ],
            },
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["accepted"] == 1
    assert body["skipped"] == 1
    assert len(body["inbox_ids"]) == 1

    from app.core.db import session_for_tenant

    async with session_for_tenant(tenant_id) as session:
        row = (
            await session.execute(
                text(
                    "SELECT ingest_channel, ingest_metadata->>'sender_email' "
                    "FROM documents_inbox WHERE inbox_id = :id"
                ),
                {"id": body["inbox_ids"][0]},
            )
        ).first()
        assert row is not None
        assert row[0] == "email"
        assert row[1] == "officer@gst.gov.in"


@pytest.mark.asyncio
async def test_unknown_slug_returns_200_skipped() -> None:
    from app.main import app

    pdf = b"%PDF-1.4 stub" + b"\0" * 200
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/v1/email/inbound",
            headers={"X-Webhook-Secret": "shh"},
            json={
                "sender": "x@y.in",
                "recipient": "notices+nonexistent-firm@noticedesk.in",
                "attachments": [
                    {
                        "filename": "x.pdf",
                        "mime_type": "application/pdf",
                        "content_b64": base64.b64encode(pdf).decode(),
                    }
                ],
            },
        )
    assert resp.status_code == 200
    assert resp.json() == {"accepted": 0, "skipped": 1, "inbox_ids": []}


@pytest.mark.asyncio
async def test_rejects_bad_secret() -> None:
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/v1/email/inbound",
            headers={"X-Webhook-Secret": "wrong"},
            json={
                "sender": "x@y.in",
                "recipient": "notices+x@noticedesk.in",
                "attachments": [],
            },
        )
    assert resp.status_code == 401
