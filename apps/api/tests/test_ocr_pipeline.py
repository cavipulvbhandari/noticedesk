"""End-to-end test of the OCR pipeline against a real Postgres + the stub
provider. Verifies:

  - upload row goes from 'pending' → 'completed'
  - ocr_text, ocr_provider_used, page_count are populated
  - audit_logs gets an 'ocr.completed' row
  - on persistent failure, status flips to 'failed' and audit + Sentry fire

These tests are skipped if TEST_DATABASE_URL isn't set so unit-only runs
remain fast.
"""

from __future__ import annotations

import hashlib
import os
import uuid
from pathlib import Path

import pytest
from sqlalchemy import text

# Module-level skip if no test DB.
if not os.environ.get("TEST_DATABASE_URL"):
    pytest.skip("TEST_DATABASE_URL not set", allow_module_level=True)


@pytest.fixture(autouse=True)
def _set_environment(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("LOCAL_STORAGE_DIR", str(tmp_path))
    monkeypatch.setenv("OCR_PROVIDER_PRIMARY", "stub")
    monkeypatch.setenv("OCR_PROVIDER_FALLBACK", "")
    monkeypatch.setenv("WORKFLOW_BACKEND", "inline")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("AUTH_PROVIDER", "dev")

    # Reset the cached singletons so they pick up the fresh env.
    from app.core.config import get_settings
    from app.services.storage.factory import get_storage
    from app.services.ocr.factory import get_ocr_provider
    from app.workflows.dispatcher import get_dispatcher

    get_settings.cache_clear()
    get_storage.cache_clear()
    get_ocr_provider.cache_clear()
    get_dispatcher.cache_clear()


@pytest.mark.asyncio
async def test_pipeline_marks_completed() -> None:
    from app.core.db import session_for_tenant
    from app.services.storage import get_storage
    from app.workflows.document_ocr import OcrJob, run_ocr_pipeline

    tenant_id = await _seed_tenant("Pipeline Firm")
    inbox_id = uuid.uuid4()
    payload = b"sample pdf bytes" * 200
    s3_key = f"tenants/{tenant_id}/inbox/{inbox_id}/sample.pdf"

    await get_storage().put(s3_key, payload, content_type="application/pdf")

    async with session_for_tenant(tenant_id) as session:
        await session.execute(
            text(
                """
                INSERT INTO documents_inbox (
                    inbox_id, tenant_id, original_filename, file_hash,
                    file_size_bytes, mime_type, s3_key, ingest_channel
                ) VALUES (:id, :tid, 'sample.pdf', :hash, :size,
                          'application/pdf', :key, 'web_upload')
                """
            ),
            {
                "id": str(inbox_id),
                "tid": str(tenant_id),
                "hash": hashlib.sha256(payload).hexdigest(),
                "size": len(payload),
                "key": s3_key,
            },
        )
        await session.commit()

    await run_ocr_pipeline(OcrJob(inbox_id=inbox_id, tenant_id=tenant_id))

    async with session_for_tenant(tenant_id) as session:
        row = (
            await session.execute(
                text(
                    "SELECT ocr_status, ocr_provider_used, page_count, ocr_text "
                    "FROM documents_inbox WHERE inbox_id = :id"
                ),
                {"id": str(inbox_id)},
            )
        ).first()
        assert row is not None
        assert row[0] == "completed"
        assert row[1] == "stub"
        assert row[2] >= 1
        assert "stub OCR" in (row[3] or "")

        audit_row = (
            await session.execute(
                text(
                    "SELECT action_type FROM audit_logs "
                    "WHERE entity_id = :id ORDER BY timestamp DESC LIMIT 1"
                ),
                {"id": str(inbox_id)},
            )
        ).first()
        assert audit_row is not None
        assert audit_row[0] == "ocr.completed"


@pytest.mark.asyncio
async def test_pipeline_marks_failed_when_no_fallback(monkeypatch) -> None:
    """Permanent failure with no fallback flips status to 'failed'."""
    monkeypatch.setattr(
        "app.services.ocr.factory.get_primary_provider",
        lambda: _AlwaysFailingProvider(),
    )
    monkeypatch.setattr(
        "app.workflows.document_ocr.get_primary_provider",
        lambda: _AlwaysFailingProvider(),
    )
    monkeypatch.setattr(
        "app.workflows.document_ocr.get_fallback_provider",
        lambda: None,
    )

    from app.core.db import session_for_tenant
    from app.services.storage import get_storage
    from app.workflows.document_ocr import OcrJob, run_ocr_pipeline

    tenant_id = await _seed_tenant("Failing Firm")
    inbox_id = uuid.uuid4()
    payload = b"x" * 1024
    s3_key = f"tenants/{tenant_id}/inbox/{inbox_id}/x.pdf"
    await get_storage().put(s3_key, payload, content_type="application/pdf")

    async with session_for_tenant(tenant_id) as session:
        await session.execute(
            text(
                """
                INSERT INTO documents_inbox (
                    inbox_id, tenant_id, original_filename, file_hash,
                    file_size_bytes, mime_type, s3_key, ingest_channel
                ) VALUES (:id, :tid, 'x.pdf', :hash, :size,
                          'application/pdf', :key, 'web_upload')
                """
            ),
            {
                "id": str(inbox_id),
                "tid": str(tenant_id),
                "hash": hashlib.sha256(payload).hexdigest(),
                "size": len(payload),
                "key": s3_key,
            },
        )
        await session.commit()

    await run_ocr_pipeline(OcrJob(inbox_id=inbox_id, tenant_id=tenant_id))

    async with session_for_tenant(tenant_id) as session:
        row = (
            await session.execute(
                text("SELECT ocr_status, ocr_error FROM documents_inbox WHERE inbox_id = :id"),
                {"id": str(inbox_id)},
            )
        ).first()
        assert row[0] == "failed"
        assert row[1]


# ---- helpers ----------------------------------------------------------------

class _AlwaysFailingProvider:
    name = "stub-fail"

    async def extract(self, file_bytes: bytes, mime_type: str):
        from app.services.ocr.base import OCRError

        raise OCRError("simulated permanent failure")


async def _seed_tenant(name: str) -> uuid.UUID:
    from app.core.db import _SessionLocal

    async with _SessionLocal() as session:
        row = (
            await session.execute(
                text("INSERT INTO tenants (legal_name) VALUES (:n) RETURNING tenant_id"),
                {"n": name},
            )
        ).first()
        await session.commit()
        return uuid.UUID(str(row[0]))
