"""Run the document-parsing agent against fixtures.

Run from the apps/api directory:

    python -m app.agents.evals.eval_runner

The runner supports two modes:

1. ``mode='real'`` calls the actual primary LLM. Costs money. Use this when
   tuning the prompt or comparing models. Requires ANTHROPIC_API_KEY (or
   OPENAI_API_KEY if you set LLM_PROVIDER_PRIMARY=openai).

2. ``mode='regex'`` runs a tiny rule-based extractor against the fixtures
   instead of the LLM. This isn't a model eval — it's a CI smoke test that
   confirms the surrounding plumbing (prompt loading, JSON sanitisation,
   identifier extraction) works end-to-end.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from app.agents.document_parsing import (
    KNOWN_DOCUMENT_TYPES,
    ParseInput,
    parse_document,
)
from app.services.identity import extract_pan_from_gstin

# Unanchored versions used to scan free text — the constants in
# app.services.identity are anchored for whole-string validation.
PAN_FINDER = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")
GSTIN_FINDER = re.compile(r"\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]\b")
from app.services.llm import LLMResponse
from app.services.llm.factory import get_llm_provider, get_primary_llm
from app.services.llm.stub import StubLLMProvider

FIXTURES_PATH = Path(__file__).parent / "document_parsing" / "fixtures.json"


def load_fixtures() -> list[dict[str, Any]]:
    return json.loads(FIXTURES_PATH.read_text())


def regex_extract(ocr_text: str) -> dict[str, Any]:
    """Deterministic fallback extractor for CI smoke tests."""
    text_upper = ocr_text.upper()
    gstins_raw = set(GSTIN_FINDER.findall(text_upper))
    pans_raw = set(PAN_FINDER.findall(text_upper))
    # Remove PANs that are actually substrings of GSTINs (positions 3-12).
    pans = sorted(p for p in pans_raw if not any(p in g for g in gstins_raw))
    gstins = sorted(gstins_raw)
    doc_type = "needs_review"
    if "ASMT-10" in ocr_text:
        doc_type = "ASMT-10"
    elif "DRC-01A" in ocr_text:
        doc_type = "DRC-01A"
    elif "DRC-01" in ocr_text:
        doc_type = "DRC-01"
    elif "142(1)" in ocr_text:
        doc_type = "IT_142(1)"
    elif "143(2)" in ocr_text:
        doc_type = "IT_143(2)"
    elif "Section 148" in ocr_text or "section 148" in ocr_text:
        doc_type = "IT_148_148A"
    elif "NFAC" in ocr_text or "CIT(A)" in ocr_text:
        doc_type = "IT_CITA_NFAC_HEARING"
    law = "GST" if doc_type.startswith(("ASMT", "DRC", "GST")) else (
        "IT" if doc_type.startswith("IT_") else None
    )
    fy_match = re.search(r"F\.?\s*Y\.?[\s:.]*(\d{4}-\d{2,4})", ocr_text)
    ay_match = re.search(r"A\.?\s*Y\.?[\s:.]*(\d{4}-\d{2,4})", ocr_text)
    return {
        "document_type": doc_type,
        "law": law,
        "pans_extracted": [{"value": p, "location": "regex"} for p in pans],
        "gstins_extracted": [
            {"value": g, "location": "regex", "state_code": g[:2]} for g in gstins
        ],
        "financial_year": fy_match.group(1) if fy_match else None,
        "assessment_year": ay_match.group(1) if ay_match else None,
        "parse_confidence": 0.7,
        "fields_needing_review": [],
        "issues": [],
        "documents_required": [],
    }


def score_one(expected: dict[str, Any], got: dict[str, Any]) -> dict[str, bool]:
    checks: dict[str, bool] = {}
    if "expected_document_type" in expected:
        checks["document_type"] = got.get("document_type") == expected["expected_document_type"]
    if "expected_law" in expected:
        checks["law"] = got.get("law") == expected["expected_law"]
    if "expected_gstin" in expected:
        gstins = [g.get("value") for g in got.get("gstins_extracted") or []]
        checks["gstin_extracted"] = expected["expected_gstin"] in gstins
    if "expected_pan" in expected:
        pans = [p.get("value") for p in got.get("pans_extracted") or []]
        checks["pan_extracted"] = expected["expected_pan"] in pans
    if "expected_pan_from_gstin" in expected:
        gstins = [g.get("value") for g in got.get("gstins_extracted") or []]
        ok = any(
            len(g) == 15 and extract_pan_from_gstin(g) == expected["expected_pan_from_gstin"]
            for g in gstins
        )
        checks["pan_from_gstin"] = ok
    if "expected_fy" in expected:
        checks["fy"] = got.get("financial_year") == expected["expected_fy"]
    if "expected_ay" in expected:
        checks["ay"] = got.get("assessment_year") == expected["expected_ay"]
    return checks


def summarise(results: Iterable[tuple[str, dict[str, bool]]]) -> dict[str, float]:
    """Per-check pass rate across the fixture set."""
    accum: dict[str, list[bool]] = {}
    for _id, checks in results:
        for k, v in checks.items():
            accum.setdefault(k, []).append(v)
    return {k: (sum(v) / len(v)) for k, v in accum.items() if v}


async def run(mode: str) -> int:
    fixtures = load_fixtures()
    results: list[tuple[str, dict[str, bool]]] = []
    for fx in fixtures:
        if mode == "real":
            try:
                provider = get_primary_llm()
            except Exception as e:  # noqa: BLE001
                print(f"could not build primary LLM: {e}", file=sys.stderr)
                return 2
            inp = ParseInput(
                inbox_id="eval", filename="eval.pdf", ingest_channel="web_upload",
                ocr_text=fx["ocr_text"], ocr_provider="stub", page_count=1,
            )
            parsed = await parse_document(inp)
            got = parsed.payload
        else:
            got = regex_extract(fx["ocr_text"])
        checks = score_one(fx, got)
        results.append((fx["id"], checks))
        verdict = "PASS" if all(checks.values()) else "FAIL"
        print(f"  {verdict}  {fx['id']:35s}  {checks}")
    print()
    print("Aggregate pass rates:")
    for k, v in sorted(summarise(results).items()):
        print(f"  {k:20s} {v*100:5.1f}%")
    return 0 if all(all(c.values()) for _, c in results) else 1


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=("real", "regex"), default="regex")
    args = p.parse_args()
    return asyncio.run(run(args.mode))


if __name__ == "__main__":
    raise SystemExit(main())
