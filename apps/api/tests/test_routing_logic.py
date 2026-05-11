"""Unit tests for the rule-based Notice Routing Agent.

These tests don't need an LLM and don't need a DB — they exercise
:func:`_resolve_canonical_pan`, the Step A logic that decides routing
outcomes from a parsed payload.
"""

from __future__ import annotations

import pytest

from app.agents.notice_routing import _resolve_canonical_pan


def parsed(law=None, pans=None, gstins=None):
    return {
        "law": law,
        "pans_extracted": [{"value": p, "location": ""} for p in (pans or [])],
        "gstins_extracted": [
            {"value": g, "location": "", "state_code": g[:2]} for g in (gstins or [])
        ],
    }


class TestStepA:
    def test_it_with_pan_only(self):
        pan, ident, anomaly = _resolve_canonical_pan(
            parsed(law="IT", pans=["AAACA9876B"])
        )
        assert pan == "AAACA9876B"
        assert ident == "AAACA9876B"
        assert anomaly is None

    def test_gst_with_gstin_only(self):
        pan, ident, anomaly = _resolve_canonical_pan(
            parsed(law="GST", gstins=["27AAACA9876B1Z5"])
        )
        assert pan == "AAACA9876B"
        assert ident == "27AAACA9876B1Z5"
        assert anomaly is None

    def test_gst_with_matching_pan_and_gstin(self):
        pan, ident, anomaly = _resolve_canonical_pan(
            parsed(law="GST", pans=["AAACA9876B"], gstins=["27AAACA9876B1Z5"])
        )
        assert pan == "AAACA9876B"
        assert ident == "27AAACA9876B1Z5"
        assert anomaly is None

    def test_mismatch_blocks_routing(self):
        pan, ident, anomaly = _resolve_canonical_pan(
            parsed(law="GST", pans=["ZZZZZ9999Z"], gstins=["27AAACA9876B1Z5"])
        )
        assert anomaly is not None
        assert anomaly["status"] == "pan_gstin_mismatch"
        assert anomaly["details"]["extracted_pan"] == "ZZZZZ9999Z"
        assert anomaly["details"]["gstin_pan_portion"] == "AAACA9876B"

    def test_no_identifiers(self):
        pan, ident, anomaly = _resolve_canonical_pan(parsed(law="GST"))
        assert anomaly is not None
        assert anomaly["status"] == "no_identifier_found"

    @pytest.mark.parametrize(
        ("gstin_pan", "extracted_pan"),
        [
            ("AAACA9876B", "AAACA9876B"),     # match
            ("AAACA9876B", "AAACA9876A"),     # one-char drift → mismatch
            ("AAACA9876B", "ZZZZZ9999Z"),     # totally different
        ],
    )
    def test_mismatch_zero_false_negatives(self, gstin_pan, extracted_pan):
        # Construct a syntactically valid GSTIN with embedded gstin_pan.
        gstin = "27" + gstin_pan + "1Z5"
        _, _, anomaly = _resolve_canonical_pan(
            parsed(law="GST", pans=[extracted_pan], gstins=[gstin])
        )
        if gstin_pan == extracted_pan:
            assert anomaly is None
        else:
            assert anomaly is not None
            assert anomaly["status"] == "pan_gstin_mismatch"

    def test_law_fallback_uses_available_identifier(self):
        # law is null but a valid GSTIN is present — still try to route.
        pan, ident, anomaly = _resolve_canonical_pan(
            parsed(law=None, gstins=["27AAACA9876B1Z5"])
        )
        assert anomaly is None
        assert pan == "AAACA9876B"

    def test_garbage_pan_is_ignored(self):
        _, _, anomaly = _resolve_canonical_pan(
            parsed(law="IT", pans=["NOT-A-PAN"])
        )
        # falls through to "no_identifier_found"
        assert anomaly is not None
        assert anomaly["status"] == "no_identifier_found"
