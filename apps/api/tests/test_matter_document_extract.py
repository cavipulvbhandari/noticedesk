"""Unit tests for the upload-time text-extraction helper.

The helper sits inside the matter-document upload route and is the bridge
between Sprint 5's pluggable OCR provider and the documents.extracted_text
column the drafting / triage agents read. Covers the four code paths:

  - text/plain   → UTF-8 decode, no OCR call
  - application/pdf → OCR provider invoked, text returned
  - office docs (docx/xlsx) → returns None without calling OCR
  - OCR error    → returns None (non-fatal); caller persists null text

The helper itself does no DB work, so these tests run without a database.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.routes.documents_matters import _extract_text
from app.services.ocr.stub import StubOCRProvider


@pytest.mark.asyncio
async def test_plaintext_is_decoded_without_ocr_call(monkeypatch) -> None:
    called: list[tuple[bytes, str]] = []

    class TrackingProvider(StubOCRProvider):
        async def extract(self, file_bytes: bytes, mime_type: str):  # type: ignore[override]
            called.append((file_bytes, mime_type))
            return await super().extract(file_bytes, mime_type)

    monkeypatch.setattr(
        "app.routes.documents_matters.get_primary_provider",
        lambda: TrackingProvider(),
    )

    result = await _extract_text(
        b"line one\nline two\n", "text/plain", document_id=uuid4()
    )
    assert result == "line one\nline two\n"
    assert called == [], "OCR provider must not be invoked for text/plain"


@pytest.mark.asyncio
async def test_pdf_runs_ocr_provider(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.routes.documents_matters.get_primary_provider",
        lambda: StubOCRProvider(),
    )
    result = await _extract_text(
        b"%PDF-1.4 fake notice", "application/pdf", document_id=uuid4()
    )
    assert result is not None
    assert "stub OCR" in result


@pytest.mark.asyncio
async def test_office_docs_return_none_without_ocr(monkeypatch) -> None:
    called: list[tuple[bytes, str]] = []

    class TrackingProvider(StubOCRProvider):
        async def extract(self, file_bytes: bytes, mime_type: str):  # type: ignore[override]
            called.append((file_bytes, mime_type))
            return await super().extract(file_bytes, mime_type)

    monkeypatch.setattr(
        "app.routes.documents_matters.get_primary_provider",
        lambda: TrackingProvider(),
    )
    result = await _extract_text(
        b"PK\x03\x04 (zip-magic for docx)",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        document_id=uuid4(),
    )
    assert result is None
    assert called == [], "office mime must not invoke OCR"


@pytest.mark.asyncio
async def test_ocr_failure_is_swallowed(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.routes.documents_matters.get_primary_provider",
        lambda: StubOCRProvider(fail_with="simulated provider outage"),
    )
    result = await _extract_text(
        b"any bytes", "application/pdf", document_id=uuid4()
    )
    assert result is None
