"""SelfHostedOCRProvider tests.

Uses httpx's MockTransport so we exercise the real request/response mapping
without standing up the Java service. The contract mirror lives in
``apps/ocr-service`` — keep these two in sync when the wire format changes.
"""

from __future__ import annotations

import httpx
import pytest

from app.services.ocr.base import ExtractedDoc, OCRError, OCRTransientError
from app.services.ocr.self_hosted import SelfHostedOCRProvider

_OK_BODY = {
    "text": "ASSESSMENT NOTICE\fPAGE TWO",
    "pageCount": 2,
    "engine": "tesseract",
    "meanConfidence": 91.4,
    "layout": {
        "pages": [
            {
                "pageNumber": 1,
                "width": 2480,
                "height": 3508,
                "meanConfidence": 91.4,
                "words": [
                    {
                        "text": "NOTICE",
                        "confidence": 95.2,
                        "box": {"x": 10, "y": 20, "width": 100, "height": 30},
                    }
                ],
            }
        ]
    },
}


def _provider_with(handler) -> SelfHostedOCRProvider:
    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport, base_url="http://ocr.test")
    return SelfHostedOCRProvider(base_url="http://ocr.test", client=client)


@pytest.mark.asyncio
async def test_extract_maps_success_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/extract"
        assert request.method == "POST"
        # multipart body carries the file part
        assert b"document" in request.content or b"form-data" in request.content
        return httpx.Response(200, json=_OK_BODY)

    provider = _provider_with(handler)
    result = await provider.extract(b"%PDF-1.4 ...", "application/pdf")

    assert isinstance(result, ExtractedDoc)
    assert result.provider_name == "self_hosted"
    assert result.page_count == 2
    assert result.text == "ASSESSMENT NOTICE\fPAGE TWO"
    assert result.layout_json["engine"] == "tesseract"
    assert result.layout_json["mean_confidence"] == 91.4
    assert result.layout_json["layout"]["pages"][0]["words"][0]["text"] == "NOTICE"


@pytest.mark.asyncio
async def test_5xx_is_transient() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "transient", "message": "pool saturated"})

    provider = _provider_with(handler)
    with pytest.raises(OCRTransientError):
        await provider.extract(b"x", "application/pdf")


@pytest.mark.asyncio
async def test_4xx_is_permanent() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(422, json={"error": "permanent", "message": "corrupt file"})

    provider = _provider_with(handler)
    with pytest.raises(OCRError) as exc:
        await provider.extract(b"x", "application/pdf")
    assert not isinstance(exc.value, OCRTransientError)


@pytest.mark.asyncio
async def test_timeout_is_transient() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    provider = _provider_with(handler)
    with pytest.raises(OCRTransientError):
        await provider.extract(b"x", "application/pdf")


@pytest.mark.asyncio
async def test_connection_error_is_transient() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    provider = _provider_with(handler)
    with pytest.raises(OCRTransientError):
        await provider.extract(b"x", "application/pdf")
