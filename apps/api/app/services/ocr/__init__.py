"""Vendor-abstracted OCR.

Sprint 1 ADR-0003 says no module hard-codes a specific OCR vendor. Sprint 2
ships two implementations (Google Document AI as primary, Azure Document
Intelligence as fallback) plus a stub for tests, all behind the same
:class:`OCRProvider` interface. The factory selects the right one from
``OCR_PROVIDER_PRIMARY`` / ``OCR_PROVIDER_FALLBACK``.
"""

from app.services.ocr.base import (
    ExtractedDoc,
    OCRError,
    OCRProvider,
    OCRTransientError,
)
from app.services.ocr.factory import (
    KNOWN_PROVIDERS,
    get_fallback_provider,
    get_ocr_provider,
    get_primary_provider,
)

__all__ = [
    "ExtractedDoc",
    "KNOWN_PROVIDERS",
    "OCRError",
    "OCRProvider",
    "OCRTransientError",
    "get_fallback_provider",
    "get_ocr_provider",
    "get_primary_provider",
]
