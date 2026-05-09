"""OCR provider contract."""

from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Any


class OCRError(Exception):
    """Permanent OCR failure that will not improve on retry."""


class OCRTransientError(OCRError):
    """Temporary failure (timeout, 5xx, throttling) — safe to retry."""


@dataclass(frozen=True, slots=True)
class ExtractedDoc:
    """Output of a single OCR pass."""

    text: str
    layout_json: dict[str, Any]
    page_count: int
    provider_name: str


class OCRProvider(abc.ABC):
    """Async OCR provider interface."""

    name: str

    @abc.abstractmethod
    async def extract(self, file_bytes: bytes, mime_type: str) -> ExtractedDoc:
        ...
