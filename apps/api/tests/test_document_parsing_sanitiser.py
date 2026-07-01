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


def test_field_confidences_always_present_for_every_canonical_field():
    from app.agents.document_parsing import _CONFIDENCE_FIELDS

    out = _sanitize({"document_type": "ASMT-10", "parse_confidence": 0.8})
    assert set(out["field_confidences"]) == set(_CONFIDENCE_FIELDS)
    # No model-supplied scores → every field falls back to parse_confidence.
    assert all(v == 0.8 for v in out["field_confidences"].values())


def test_field_confidences_honour_valid_model_scores():
    out = _sanitize({
        "document_type": "ASMT-10",
        "parse_confidence": 0.9,
        "field_confidences": {
            "demand_amount": 0.62,
            "authority": 0.55,
        },
    })
    assert out["field_confidences"]["demand_amount"] == 0.62
    assert out["field_confidences"]["authority"] == 0.55
    # Unscored fields still fall back to the document-level confidence.
    assert out["field_confidences"]["document_type"] == 0.9


def test_field_confidences_forced_low_for_review_fields():
    out = _sanitize({
        "document_type": "ASMT-10",
        "parse_confidence": 0.95,
        "due_date": "not a date",           # → flagged for review
        "field_confidences": {"due_date": 0.99},  # model over-claims
    })
    assert "due_date" in out["fields_needing_review"]
    # A field we couldn't trust must never read as confident.
    assert out["field_confidences"]["due_date"] == 0.0


def test_field_confidences_reject_out_of_range_and_bools():
    out = _sanitize({
        "document_type": "ASMT-10",
        "parse_confidence": 0.7,
        "field_confidences": {
            "demand_amount": 4.2,      # > 1.0 → rejected
            "authority": True,         # bool → rejected
            "notice_number": "0.9",    # string → rejected
        },
    })
    fc = out["field_confidences"]
    assert fc["demand_amount"] == 0.7
    assert fc["authority"] == 0.7
    assert fc["notice_number"] == 0.7


def test_field_confidences_ignore_unknown_keys():
    out = _sanitize({
        "document_type": "ASMT-10",
        "parse_confidence": 0.5,
        "field_confidences": {"totally_made_up": 0.9},
    })
    assert "totally_made_up" not in out["field_confidences"]


def null_str():
    return None
