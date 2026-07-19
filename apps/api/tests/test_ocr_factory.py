"""OCR provider factory tests.

Switching primary from google_doc_ai to azure_doc_intel must be a config-only
change — that's the acceptance criterion for vendor abstraction.
"""

from __future__ import annotations

import pytest

from app.core.config import Settings
from app.services.ocr import KNOWN_PROVIDERS
from app.services.ocr.factory import get_ocr_provider
from app.services.ocr.stub import StubOCRProvider


def test_known_providers() -> None:
    assert KNOWN_PROVIDERS == frozenset(
        {"google_doc_ai", "azure_doc_intel", "self_hosted", "stub"}
    )


def test_self_hosted_requires_url() -> None:
    get_ocr_provider.cache_clear()
    from app.core.config import get_settings
    from app.services.ocr.base import OCRError

    get_settings.cache_clear()
    import os

    prev = os.environ.pop("SELF_HOSTED_OCR_URL", None)
    try:
        with pytest.raises(OCRError):
            get_ocr_provider("self_hosted")
    finally:
        if prev is not None:
            os.environ["SELF_HOSTED_OCR_URL"] = prev
        get_settings.cache_clear()
        get_ocr_provider.cache_clear()


def test_stub_factory_returns_stub() -> None:
    get_ocr_provider.cache_clear()
    provider = get_ocr_provider("stub")
    assert isinstance(provider, StubOCRProvider)
    assert provider.name == "stub"


def test_unknown_provider_raises() -> None:
    get_ocr_provider.cache_clear()
    from app.services.ocr.base import OCRError

    with pytest.raises(OCRError):
        get_ocr_provider("nonexistent")


def test_settings_select_provider_by_name() -> None:
    s = Settings(ocr_provider_primary="stub")
    assert s.ocr_provider_primary == "stub"

    s2 = Settings(ocr_provider_primary="google_doc_ai", ocr_provider_fallback="azure_doc_intel")
    assert s2.ocr_provider_primary == "google_doc_ai"
    assert s2.ocr_provider_fallback == "azure_doc_intel"
