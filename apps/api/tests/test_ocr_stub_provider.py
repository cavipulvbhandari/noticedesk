from __future__ import annotations

import pytest

from app.services.ocr.base import ExtractedDoc, OCRError
from app.services.ocr.stub import StubOCRProvider


@pytest.mark.asyncio
async def test_stub_returns_extracted_doc() -> None:
    provider = StubOCRProvider()
    result = await provider.extract(b"some bytes that look like a notice", "application/pdf")
    assert isinstance(result, ExtractedDoc)
    assert result.provider_name == "stub"
    assert result.page_count >= 1
    assert "stub OCR" in result.text


@pytest.mark.asyncio
async def test_stub_can_simulate_failure() -> None:
    provider = StubOCRProvider(fail_with="boom")
    with pytest.raises(OCRError):
        await provider.extract(b"x", "application/pdf")
