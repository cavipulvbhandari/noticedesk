"""Unit tests for the parsing-agent sanitiser.

These don't need an LLM — they exercise the `_sanitize` function that
validates and normalizes whatever the model returns.
"""

from __future__ import annotations

from app.agents.document_parsing import _sanitize


def test_clamps_unknown_document_type():
    out = _sanitize({"document_type": "DRC-99", "law": "GST"})
    assert out["document_type"] == "needs_review"
    assert "document_type" in out["fields_needing_review"]


def test_forces_law_for_known_doc_type():
    out = _sanitize({"document_type": "ASMT-10", "law": "IT"})  # contradiction
    assert out["law"] == "GST"  # snapped to GST based on doc type
    out2 = _sanitize({"document_type": "IT_142(1)", "law": null_str()})
    assert out2["law"] == "IT"


def test_drops_fabricated_pan():
    out = _sanitize({
        "document_type": "IT_142(1)",
        "pans_extracted": [
            {"value": "AAACX1234F", "location": "para 1"},     # valid
            {"value": "PRETEND-PAN", "location": "para 2"},    # invalid
            {"value": "AAACX1234F", "location": "para 1"},     # dup
        ],
    })
    assert len(out["pans_extracted"]) == 1
    assert out["pans_extracted"][0]["value"] == "AAACX1234F"


def test_drops_fabricated_gstin():
    out = _sanitize({
        "document_type": "ASMT-10",
        "gstins_extracted": [
            {"value": "27AAACA9876B1Z5", "location": "header"},     # valid
            {"value": "27aaaca9876b1z5", "location": "lowercase"},  # invalid case
            {"value": "ZZ-NOT-A-GSTIN-ZZ", "location": "x"},        # garbage
        ],
    })
    # The lowercase one gets normalized to upper and dedup'd against the first
    assert len(out["gstins_extracted"]) == 1
    assert out["gstins_extracted"][0]["value"] == "27AAACA9876B1Z5"


def test_normalises_indian_dates():
    out = _sanitize({
        "document_type": "ASMT-10",
        "issue_date": "12-09-2024",        # DD-MM-YYYY (Indian)
        "due_date": "2024-09-30",          # already ISO
        "hearing_date": "31/12/24",        # DD/MM/YY
        "receipt_date": "not a date",
    })
    assert out["issue_date"] == "2024-09-12"
    assert out["due_date"] == "2024-09-30"
    assert out["hearing_date"] == "2024-12-31"
    assert out["receipt_date"] is None
    assert "receipt_date" in out["fields_needing_review"]


def test_normalises_year_ranges():
    out = _sanitize({
        "document_type": "ASMT-10",
        "financial_year": "2022 - 2023",
        "assessment_year": "2023-24",
    })
    assert out["financial_year"] == "2022-23"
    assert out["assessment_year"] == "2023-24"


def test_demand_amount_strips_punctuation():
    out = _sanitize({
        "document_type": "DRC-01",
        "demand_amount": "Rs 1,84,500/-",
    })
    assert out["demand_amount"] == 184500.0


def test_clamps_confidence():
    out = _sanitize({"document_type": "ASMT-10", "parse_confidence": 17.0})
    assert out["parse_confidence"] == 0.0
    assert "parse_confidence" in out["fields_needing_review"]


def null_str():
    return None
