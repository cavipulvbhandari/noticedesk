"""Canned parser responses for offline dev (LLM_PROVIDER_PRIMARY=stub).

The stub OCR provider returns text with no real identifiers, so the parsing
agent has nothing to extract. This module returns plausible canned JSON keyed
off the original filename embedded in the parsing-agent user prompt, so the
parse-and-route pipeline produces real-looking outcomes in offline dev.

Replace with a real LLM provider for parser-quality testing — identifiers
hard-coded here must match the dev DB seed.
"""

from __future__ import annotations

import json
from typing import Any

_CANNED_BY_FILENAME: dict[str, dict[str, Any]] = {
    "drc-01.pdf": {
        "document_type": "DRC-01A",
        "client_name_on_document": "Sunrise Papers Pvt Ltd",
        "pans_extracted": [{"value": "AAQCS3456P", "location": "header"}],
        "gstins_extracted": [
            {"value": "27AAQCS3456P1ZF", "location": "header", "state_code": "27"}
        ],
        "notice_number": "ZA270526123456",
        "din_or_rfn": "DIN-202604-000123",
        "issue_date": "2026-04-15",
        "receipt_date": "2026-04-20",
        "due_date": "2026-05-15",
        "hearing_date": None,
        "financial_year": "2023-24",
        "assessment_year": None,
        "authority": "Assistant Commissioner, CGST Mumbai West",
        "demand_amount": 245000,
        "issues": ["Mismatch between GSTR-3B and GSTR-1 for Q2 FY 2023-24"],
        "documents_required": ["GSTR-3B reconciliation", "Invoice-level supporting"],
        "parse_confidence": 0.92,
        "fields_needing_review": [],
    },
    "GST Notice.pdf": {
        "document_type": "ASMT-10",
        "client_name_on_document": "Acme Industries Private Limited",
        "pans_extracted": [{"value": "AAACA9876B", "location": "header"}],
        "gstins_extracted": [
            {"value": "27AAACA9876B1Z5", "location": "header", "state_code": "27"}
        ],
        "notice_number": "ASMT10-MH-2026-00789",
        "din_or_rfn": "DIN-202604-000789",
        "issue_date": "2026-04-22",
        "receipt_date": "2026-04-25",
        "due_date": "2026-05-22",
        "hearing_date": None,
        "financial_year": "2022-23",
        "assessment_year": None,
        "authority": "Deputy Commissioner of State Tax, Mumbai",
        "demand_amount": 1850000,
        "issues": ["ITC reconciliation discrepancy with GSTR-2A"],
        "documents_required": ["GSTR-2A reconciliation", "Tax invoices for inward supplies"],
        "parse_confidence": 0.90,
        "fields_needing_review": [],
    },
}


def lookup_canned_response(user_prompt: str) -> str | None:
    """Return canned JSON string for the filename embedded in the user prompt.

    The parsing agent's user template includes the original filename verbatim,
    so substring match is enough. Returns None if no canned entry exists, in
    which case the caller falls back to the StubLLMProvider default of "{}".
    """
    for filename, payload in _CANNED_BY_FILENAME.items():
        if filename in user_prompt:
            return json.dumps(payload)
    return None
