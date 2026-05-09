"""Google Document AI provider.

This file holds the integration shape; the live SDK call is wrapped in
:meth:`_call_api` so tests can stub it without faking the whole class. Call
sites get an :class:`OCRProvider`; they don't import google.cloud.documentai
directly.
"""

from __future__ import annotations

import asyncio
from typing import Any

from app.services.ocr.base import (
    ExtractedDoc,
    OCRError,
    OCRProvider,
    OCRTransientError,
)


class GoogleDocumentAIProvider(OCRProvider):
    name = "google_doc_ai"

    def __init__(
        self,
        *,
        project_id: str,
        location: str,
        processor_id: str,
        client: Any | None = None,
        timeout_seconds: float = 60.0,
    ) -> None:
        self._project_id = project_id
        self._location = location
        self._processor_id = processor_id
        self._client = client
        self._timeout = timeout_seconds

    async def extract(self, file_bytes: bytes, mime_type: str) -> ExtractedDoc:
        try:
            text, layout, pages = await asyncio.wait_for(
                self._call_api(file_bytes, mime_type),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError as e:
            raise OCRTransientError(f"google_doc_ai timed out after {self._timeout}s") from e
        return ExtractedDoc(
            text=text,
            layout_json=layout,
            page_count=pages,
            provider_name=self.name,
        )

    async def _call_api(
        self, file_bytes: bytes, mime_type: str
    ) -> tuple[str, dict[str, Any], int]:
        client = self._client
        if client is None:
            try:
                from google.cloud import documentai_v1 as documentai  # type: ignore[import-not-found]
            except ImportError as e:
                raise OCRError(
                    "google-cloud-documentai not installed; either install it or "
                    "switch OCR_PROVIDER_PRIMARY to a different provider"
                ) from e
            client = documentai.DocumentProcessorServiceAsyncClient()
            self._client = client

        name = (
            f"projects/{self._project_id}/locations/{self._location}"
            f"/processors/{self._processor_id}"
        )
        try:
            from google.cloud.documentai_v1 import (  # type: ignore[import-not-found]
                ProcessRequest,
                RawDocument,
            )
        except ImportError as e:  # pragma: no cover — exercised only when SDK is missing
            raise OCRError("google-cloud-documentai not installed") from e

        request = ProcessRequest(
            name=name,
            raw_document=RawDocument(content=file_bytes, mime_type=mime_type),
        )
        try:
            response = await client.process_document(request=request)
        except Exception as e:  # noqa: BLE001
            # Treat all SDK exceptions as transient by default — Google's
            # error taxonomy is large and we'd rather retry than fail closed.
            raise OCRTransientError(f"google_doc_ai call failed: {e}") from e

        document = response.document
        return (
            document.text or "",
            {"raw": str(document)},
            len(document.pages) if document.pages else 0,
        )
