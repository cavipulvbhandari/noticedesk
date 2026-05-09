"""Deterministic OCR provider used by tests and local dev.

Returns plausible-looking text derived from the input bytes so tests can
verify the workflow without a real OCR vendor. Selectable via
``OCR_PROVIDER_PRIMARY=stub`` or ``OCR_PROVIDER_FALLBACK=stub``.
"""

from __future__ import annotations

import hashlib

from app.services.ocr.base import ExtractedDoc, OCRError, OCRProvider


class StubOCRProvider(OCRProvider):
    name = "stub"

    def __init__(self, *, fail_with: str | None = None) -> None:
        self._fail_with = fail_with

    async def extract(self, file_bytes: bytes, mime_type: str) -> ExtractedDoc:
        if self._fail_with:
            raise OCRError(self._fail_with)
        digest = hashlib.sha256(file_bytes).hexdigest()
        text = (
            "[stub OCR] notice text\n"
            f"size_bytes={len(file_bytes)}\n"
            f"mime_type={mime_type}\n"
            f"sha256={digest}\n"
        )
        return ExtractedDoc(
            text=text,
            layout_json={"stub": True, "sha256": digest},
            # Fake page count: assume 1 page per ~3 KB so tests can pass an
            # arbitrary buffer and get a plausible page total.
            page_count=max(1, len(file_bytes) // 3000),
            provider_name=self.name,
        )
