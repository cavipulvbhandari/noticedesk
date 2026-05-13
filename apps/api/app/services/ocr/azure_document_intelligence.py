"""Azure Document Intelligence provider (fallback)."""

from __future__ import annotations

import asyncio
from typing import Any

from app.services.ocr.base import (
    ExtractedDoc,
    OCRError,
    OCRProvider,
    OCRTransientError,
)


class AzureDocumentIntelligenceProvider(OCRProvider):
    name = "azure_doc_intel"

    def __init__(
        self,
        *,
        endpoint: str,
        api_key: str,
        model_id: str = "prebuilt-document",
        client: Any | None = None,
        timeout_seconds: float = 60.0,
    ) -> None:
        self._endpoint = endpoint
        self._api_key = api_key
        self._model_id = model_id
        self._client = client
        self._timeout = timeout_seconds

    async def extract(self, file_bytes: bytes, mime_type: str) -> ExtractedDoc:
        try:
            text, layout, pages = await asyncio.wait_for(
                self._call_api(file_bytes, mime_type),
                timeout=self._timeout,
            )
        except TimeoutError as e:
            raise OCRTransientError(f"azure_doc_intel timed out after {self._timeout}s") from e
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
                from azure.ai.documentintelligence.aio import (  # type: ignore[import-not-found]
                    DocumentIntelligenceClient,
                )
                from azure.core.credentials import (
                    AzureKeyCredential,  # type: ignore[import-not-found]
                )
            except ImportError as e:
                raise OCRError(
                    "azure-ai-documentintelligence not installed; either install it "
                    "or switch OCR_PROVIDER_FALLBACK to a different provider"
                ) from e
            client = DocumentIntelligenceClient(
                endpoint=self._endpoint,
                credential=AzureKeyCredential(self._api_key),
            )
            self._client = client

        try:
            poller = await client.begin_analyze_document(
                self._model_id,
                analyze_request=file_bytes,
                content_type=mime_type,
            )
            result = await poller.result()
        except Exception as e:  # noqa: BLE001
            raise OCRTransientError(f"azure_doc_intel call failed: {e}") from e

        text = getattr(result, "content", "") or ""
        pages = len(getattr(result, "pages", []) or [])
        return text, {"raw": _to_dict(result)}, pages


def _to_dict(result: Any) -> dict[str, Any]:
    if hasattr(result, "as_dict"):
        return dict(result.as_dict())
    return {"repr": repr(result)}
