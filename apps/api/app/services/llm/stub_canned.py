"""Canned parser + drafting responses for offline dev (LLM_PROVIDER_PRIMARY=stub).

The stub OCR provider returns text with no real identifiers, so the parsing
agent has nothing to extract. This module returns plausible canned JSON keyed
off the original filename embedded in the parsing-agent user prompt, so the
parse-and-route pipeline produces real-looking outcomes in offline dev.

The drafting agent (Sprint 5) also routes through here: when the stub provider
is selected, ``_drafting_canned`` assembles a deterministic 15-section reply
draft from the matter context inside the prompt. The output exercises every
downstream code path (citation extraction, verification, paragraph map, Word
export) without requiring an Anthropic key.

Replace with a real LLM provider for parser-quality or draft-quality testing —
identifiers hard-coded here must match the dev DB seed.
"""

from __future__ import annotations

import json
import re
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
    """Return canned JSON string for the agent that issued this prompt.

    Routing priority:
      1. Drafting agent (Sprint 5) — recognised by the "MATTER CONTEXT" header.
      2. Document parsing agent (Sprint 3) — keyed off the original filename.

    Demo fallback: when ``STUB_DEFAULT_CANNED`` is set (e.g. to
    ``acme_mh_asmt10``), any parsing prompt that doesn't match a specific
    filename falls back to the named canned entry. This lets a partner drop
    *any* PDF onto /inbox and watch the whole route+draft flow without
    renaming the file to "GST Notice.pdf" first.

    Returns None if no entry matches and no fallback is configured, in which
    case the caller falls back to the StubLLMProvider default of "{}".
    """
    if "MATTER CONTEXT" in user_prompt:
        return _drafting_canned(user_prompt)
    for filename, payload in _CANNED_BY_FILENAME.items():
        if filename in user_prompt:
            return json.dumps(payload)

    fallback_key = __import__("os").environ.get("STUB_DEFAULT_CANNED", "").strip()
    if fallback_key:
        payload = _FALLBACK_BY_KEY.get(fallback_key)
        if payload is not None:
            return json.dumps(payload)
    return None


# Friendly keys for the STUB_DEFAULT_CANNED env var. Pick whichever matches
# the matter you want every uploaded PDF to route to during a demo.
_FALLBACK_BY_KEY: dict[str, dict[str, Any]] = {
    "acme_mh_asmt10": _CANNED_BY_FILENAME["GST Notice.pdf"],
    "drc01a_anomaly": _CANNED_BY_FILENAME["drc-01.pdf"],
}


# ---- Drafting-agent canned responses --------------------------------------


def _drafting_canned(user_prompt: str) -> str:
    """Build a deterministic 15-section draft from the prompt.

    The stub doesn't ship pre-canned response strings per notice because the
    matter pool grows over time; instead it parses the registration identifier
    + notice type out of the user prompt and assembles a generic-but-plausible
    draft so the workflow end-to-end exercises every code path. Real Anthropic
    output looks materially different and partners should always run with a
    real provider in front of clients.
    """
    notice_type = _extract_after(user_prompt, "Type: ") or "GST notice"
    legal_name = (
        _extract_after(user_prompt, "Client: ").split(" (")[0]
        if "Client: " in user_prompt
        else "the assessee"
    )
    pan = _extract_pan(user_prompt) or "—"
    reg = _extract_after(user_prompt, "Registration: ") or "—"
    fy_or_ay = _extract_after(user_prompt, "Financial year / Assessment year: ") or "—"
    tone = _extract_after(user_prompt, "Tone: ") or "formal"
    authority = _extract_after(user_prompt, "Authority: ") or "the learned officer"
    due_date = _extract_after(user_prompt, "Due date: ") or "—"

    is_hearing = "HEARING" in notice_type.upper()

    def p(html: str) -> str:
        return f"<p>{html}</p>"

    def cite(case: str, prop: str) -> str:
        return (
            f'<span class="draft-citation" data-status="VERIFIED">{case}</span>'
            f" for the proposition that {prop}"
        )

    sections = [
        {
            "num": 1,
            "title": "Executive Summary",
            "body_html": p(
                f"This reply is filed on behalf of {legal_name} (PAN {pan}) "
                f"in response to the {notice_type} dated {due_date} issued by "
                f"{authority} for {fy_or_ay}. The notice is replied to in full; "
                "every issue raised is addressed paragraph-wise in Section 05, "
                "supported by the documents listed in Section 10."
            ),
        },
        {
            "num": 2,
            "title": "Notice Understanding",
            "body_html": p(
                f"The Department has issued a {notice_type} alleging the "
                "matters set out in the issue text. The assessee&rsquo;s "
                "position and the legal grounds in support are set out below."
            ),
        },
        {
            "num": 3,
            "title": "Factual Background",
            "body_html": p(
                f"{legal_name} holds {reg}. The relevant financial period is "
                f"{fy_or_ay}. All books of account, returns, and supporting "
                "records pertaining to this registration are maintained at "
                "the registered place of business and are available for "
                "verification. [DOCUMENT REQUESTED — pending from client]"
            ),
        },
        {
            "num": 4,
            "title": "Issue-wise Response",
            "body_html": p(
                "Issue 1 — The assessee respectfully submits that the alleged "
                "discrepancy is reconcilable on the face of the records. A "
                "detailed reconciliation is annexed."
            )
            + p(
                "Issue 2 — Without prejudice, the assessee further submits "
                "that even if any discrepancy is held to subsist, no demand "
                "can be fastened in the absence of a finding of suppression."
            ),
        },
        {
            "num": 5,
            "title": "Para-wise Reply",
            "body_html": p(
                "Para 1 — Admitted to the extent of the identity of the "
                "assessee and the registration; the rest of the para is "
                "denied as alleged."
            )
            + p(
                "Para 2 — The figures referenced in the notice are accepted; "
                "the inference drawn from them is denied for the reasons in "
                "Section 06."
            ),
        },
        {
            "num": 6,
            "title": "Legal Submissions",
            "body_html": p(
                "It is well settled that a demand under the GST / Income Tax "
                "Act cannot rest on suspicion alone — "
                + cite(
                    "Commissioner of GST v. Bharti Airtel Ltd., "
                    "(2021) 6 SCC 257, para 24",
                    "the Department bears the burden of establishing a "
                    "demand on positive material",
                )
                + ". The reasoning extends to scrutiny notices: "
                + cite(
                    "Larsen &amp; Toubro Ltd. v. State of Karnataka, "
                    "(2014) 1 SCC 708, para 18",
                    "reconciliation is sufficient response where the records "
                    "bear out the position",
                )
                + "."
            ),
        },
        {
            "num": 7,
            "title": "Procedural Objections",
            "body_html": p(
                "Without prejudice to the merits, the assessee reserves the "
                "right to raise procedural objections in case the notice is "
                "found to have been issued beyond the period of limitation "
                "prescribed under the relevant statute."
            ),
        },
    ]

    if is_hearing:
        sections.append(
            {
                "num": 8,
                "title": "Cross-Examination Request",
                "body_html": p(
                    "Insofar as the notice relies on a third-party statement, "
                    "the assessee invokes the right to cross-examine the "
                    "deponent before any reliance is placed against it. "
                    + cite(
                        "Andaman Timber Industries v. CCE, "
                        "(2015) 324 ELT 641 (SC)",
                        "denial of cross-examination of a witness whose "
                        "statement is relied upon vitiates the proceedings",
                    )
                    + "."
                ),
            }
        )

    sections.extend(
        [
            {
                "num": 10,
                "title": "Documents Enclosed",
                "body_html": p(
                    "1. Copy of the impugned notice.\n"
                    "2. Reconciliation working.\n"
                    "3. Statutory returns for the relevant period."
                ),
            },
            {
                "num": 11,
                "title": "Annexure Index",
                "body_html": p(
                    "Annexure A — Reconciliation working.\n"
                    "Annexure B — Statutory returns."
                ),
            },
            {
                "num": 12,
                "title": "Prayer",
                "body_html": p(
                    "In light of the above, it is most respectfully prayed "
                    "that the proceedings initiated vide the captioned notice "
                    "be dropped and any consequential demand be set aside."
                ),
            },
            {
                "num": 13,
                "title": "Internal Partner Note",
                "body_html": p(
                    '<span class="draft-internal-note">Officer historically '
                    "open to reconciliation-based closure. Push for personal "
                    "hearing only if reply is rejected on the first round."
                    "</span>"
                ),
            },
            {
                "num": 14,
                "title": "Client Summary",
                "body_html": p(
                    f"{legal_name}: the Department has issued a "
                    f"{notice_type} for {fy_or_ay}. We have prepared a "
                    "complete reply with the necessary reconciliation; "
                    "please review and sign so we can file before "
                    f"{due_date}."
                ),
            },
            {
                "num": 15,
                "title": "Filing Checklist",
                "body_html": p(
                    "&bull; Verify all annexures are paginated and stamped.\n"
                    "&bull; Obtain the partner&rsquo;s signature on the reply.\n"
                    "&bull; File via the GST portal acknowledgement (or email "
                    "to the listed authority address).\n"
                    "&bull; Diary the acknowledgement and update lifecycle "
                    "to Reply Submitted."
                ),
            },
        ]
    )

    payload = {
        "sections": sections,
        "internal_partner_note": (
            "Officer historically open to reconciliation-based closure. Push "
            "for personal hearing only if reply is rejected on the first "
            f"round. Tone applied: {tone}."
        ),
        "client_summary": (
            f"{legal_name}: the Department has issued a {notice_type} for "
            f"{fy_or_ay}. We have prepared a complete reply with the "
            "necessary reconciliation; please review and sign so we can "
            f"file before {due_date}."
        ),
    }
    return json.dumps(payload)


def _extract_after(haystack: str, marker: str) -> str:
    idx = haystack.find(marker)
    if idx == -1:
        return ""
    line_end = haystack.find("\n", idx)
    return haystack[idx + len(marker) : line_end if line_end != -1 else None].strip()


def _extract_pan(haystack: str) -> str | None:
    m = re.search(r"PAN ([A-Z]{5}[0-9]{4}[A-Z])", haystack)
    return m.group(1) if m else None
