"""Live-provider preflight: call Claude + Google Doc AI once each and report.

Run from apps/api:

    .venv/bin/python -m scripts.check_live_providers

Exits 0 if every configured non-stub provider responds. Run this before
the partner sits down so credential issues surface in your terminal, not
in the demo flow.
"""

from __future__ import annotations

import asyncio
import os
import sys
import time

from app.core.config import get_settings
from app.services.llm import get_primary_llm
from app.services.ocr import get_ocr_provider, get_primary_provider

# A 1-page valid PDF: "Hello from NoticeDesk" so Doc AI has actual glyphs to OCR.
_TINY_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]"
    b"/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
    b"4 0 obj<</Length 60>>stream\n"
    b"BT /F1 12 Tf 72 720 Td (Hello from NoticeDesk preflight) Tj ET\n"
    b"endstream endobj\n"
    b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
    b"xref\n0 6\n"
    b"0000000000 65535 f \n"
    b"0000000010 00000 n \n"
    b"0000000053 00000 n \n"
    b"0000000098 00000 n \n"
    b"0000000189 00000 n \n"
    b"0000000292 00000 n \n"
    b"trailer<</Size 6/Root 1 0 R>>\n"
    b"startxref\n358\n%%EOF\n"
)


GREEN = "\033[32m"
RED = "\033[31m"
RESET = "\033[0m"
DIM = "\033[2m"


def _ok(msg: str) -> None:
    print(f"  {GREEN}✓{RESET} {msg}")


def _fail(msg: str) -> None:
    print(f"  {RED}✗{RESET} {msg}")


async def _check_llm() -> bool:
    s = get_settings()
    print(f"LLM provider: {s.llm_provider_primary}")
    if s.llm_provider_primary == "stub":
        print(f"  {DIM}stub mode — set LLM_PROVIDER_PRIMARY=anthropic to flip{RESET}")
        return True
    try:
        provider = get_primary_llm()
    except Exception as e:  # noqa: BLE001
        _fail(f"could not build provider: {e}")
        return False

    if provider is None:
        _fail("get_primary_llm() returned None")
        return False

    start = time.monotonic()
    try:
        response = await provider.generate_text(
            system='Reply only with the word "ok".',
            user="health check",
            max_output_tokens=8,
            temperature=0.0,
        )
    except Exception as e:  # noqa: BLE001
        _fail(f"API call failed: {e}")
        return False
    elapsed = time.monotonic() - start
    _ok(f"{provider.name} · {provider.model} · {elapsed:.2f}s · {response.content.strip()[:40]!r}")
    if response.input_tokens is not None:
        print(
            f"    {DIM}tokens in={response.input_tokens} out={response.output_tokens}{RESET}"
        )
    return True


async def _check_ocr() -> bool:
    s = get_settings()
    print(f"OCR provider: {s.ocr_provider_primary}")
    if s.ocr_provider_primary == "stub":
        print(f"  {DIM}stub mode — set OCR_PROVIDER_PRIMARY=google_doc_ai to flip{RESET}")
        return True
    try:
        provider = get_primary_provider()
    except Exception as e:  # noqa: BLE001
        _fail(f"could not build provider: {e}")
        return False

    start = time.monotonic()
    try:
        extracted = await provider.extract(_TINY_PDF, "application/pdf")
    except Exception as e:  # noqa: BLE001
        _fail(f"API call failed: {e}")
        return False
    elapsed = time.monotonic() - start
    text_preview = (extracted.text or "").replace("\n", " ")[:60]
    _ok(
        f"{provider.name} · {elapsed:.2f}s · {extracted.page_count} pages · "
        f"text={text_preview!r}"
    )
    fallback_name = s.ocr_provider_fallback
    if fallback_name and fallback_name != s.ocr_provider_primary:
        try:
            fb = get_ocr_provider(fallback_name)
            print(f"    {DIM}fallback configured: {fb.name} (not exercised here){RESET}")
        except Exception as e:  # noqa: BLE001
            _fail(f"  fallback build failed: {e}")
            return False
    return True


def _check_citation() -> bool:
    name = os.environ.get("CITATION_PROVIDER", "stub")
    print(f"Citation provider: {name}")
    if name == "stub":
        print(f"  {DIM}stub mode — set CITATION_PROVIDER=indiankanoon to flip{RESET}")
        return True
    if not os.environ.get("INDIANKANOON_API_TOKEN"):
        _fail("INDIANKANOON_API_TOKEN is empty")
        return False
    _ok("indiankanoon · token present (no API call here — verified live during draft)")
    return True


async def main() -> int:
    print("== NoticeDesk live-provider preflight ==\n")
    results: list[bool] = []
    results.append(await _check_llm())
    print()
    results.append(await _check_ocr())
    print()
    results.append(_check_citation())
    print()

    if all(results):
        print(f"{GREEN}All configured providers responded.{RESET}")
        return 0
    print(f"{RED}One or more providers failed — fix before the partner sits down.{RESET}")
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
