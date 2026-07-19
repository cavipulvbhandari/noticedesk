"""Self-hosted OCR provider.

Calls NoticeDesk's own Tesseract-backed OCR microservice (``apps/ocr-service``)
over HTTP instead of a third-party cloud vendor. From the pipeline's point of
view it is just another :class:`OCRProvider`; selecting it is a config change
(``OCR_PROVIDER_PRIMARY=self_hosted``), exactly like the cloud providers.

The service contract (see ``apps/ocr-service/README.md``):

    POST {base_url}/v1/extract   (multipart/form-data, part ``file``)
      -> 200 {text, pageCount, engine, meanConfidence, layout}
      -> 4xx {error, message, retryable:false}   permanent
      -> 5xx {error, message, retryable:true}    transient

We map 5xx / timeouts / connection errors to :class:`OCRTransientError` so the
pipeline's retry loop kicks in, and 4xx to :class:`OCRError` (permanent).
"""

from __future__ import annotations

from typing import Any

import httpx

from app.services.ocr.base import (
    ExtractedDoc,
    OCRError,
    OCRProvider,
    OCRTransientError,
)


class SelfHostedOCRProvider(OCRProvider):
    name = "self_hosted"

    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float = 60.0,
        languages: str = "eng",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._languages = languages
        self._client = client

    async def extract(self, file_bytes: bytes, mime_type: str) -> ExtractedDoc:
        url = f"{self._base_url}/v1/extract"
        files = {"file": ("document", file_bytes, mime_type or "application/pdf")}
        data = {"languages": self._languages}

        client = self._client
        owns_client = client is None
        if client is None:
            client = httpx.AsyncClient(timeout=self._timeout)
        try:
            response = await client.post(url, files=files, data=data)
        except httpx.TimeoutException as e:
            raise OCRTransientError(
                f"self_hosted OCR timed out after {self._timeout}s"
            ) from e
        except httpx.TransportError as e:
            # DNS/connection reset/etc. — the service may just be restarting.
            raise OCRTransientError(f"self_hosted OCR connection failed: {e}") from e
        finally:
            if owns_client:
                await client.aclose()

        self._raise_for_status(response)

        try:
            payload = response.json()
        except ValueError as e:
            raise OCRError(f"self_hosted OCR returned non-JSON body: {e}") from e

        return self._to_extracted_doc(payload)

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code < 400:
            return
        detail = _safe_error_detail(response)
        if response.status_code >= 500:
            raise OCRTransientError(
                f"self_hosted OCR {response.status_code}: {detail}"
            )
        raise OCRError(f"self_hosted OCR {response.status_code}: {detail}")

    def _to_extracted_doc(self, payload: dict[str, Any]) -> ExtractedDoc:
        text = payload.get("text") or ""
        page_count = int(payload.get("pageCount") or 0)
        # Preserve the underlying engine name (e.g. "tesseract") and the full
        # layout/confidence in layout_json, but record provider_name as this
        # provider so audit rows read "self_hosted".
        layout: dict[str, Any] = {
            "engine": payload.get("engine"),
            "mean_confidence": payload.get("meanConfidence"),
            "layout": payload.get("layout") or {},
        }
        return ExtractedDoc(
            text=text,
            layout_json=layout,
            page_count=page_count,
            provider_name=self.name,
        )


def _safe_error_detail(response: httpx.Response) -> str:
    try:
        body = response.json()
        if isinstance(body, dict):
            return str(body.get("message") or body.get("error") or body)
        return str(body)
    except ValueError:
        return response.text[:500]
