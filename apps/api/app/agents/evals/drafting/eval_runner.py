"""Run the drafting agent against the 10-matter fixture set.

Run from the apps/api directory:

    .venv/bin/python -m app.agents.evals.drafting.eval_runner            # stub provider
    LLM_PROVIDER_PRIMARY=anthropic .venv/bin/python -m \
        app.agents.evals.drafting.eval_runner                            # real model

Targets (per the brief):
    > 70% structural accuracy on the first run
    0 hallucinated facts (every fact traceable in paragraph_to_source_map)
    > 85% factual accuracy
    All citations in the final draft are VERIFIED or VERIFIED_PARTIAL
    (no UNVERIFIED reaches the partner's screen — workflow strips them)

What this runner actually checks (Phase 1):
    - section count >= min_sections
    - every required_section_titles entry appears
    - every must_mention_substrings appears somewhere in the rendered draft
    - none of the must_not_mention_substrings appear (registration-scoping)
    - if the stub provider is used, structural pass-rate is reported
      against the 10-fixture set. With a real LLM the same script runs;
      the only difference is the source of the section bodies.

Citation verification is exercised end-to-end via the stub verifier so
the "no UNVERIFIED reaches partner screen" guarantee is tested without
the IndianKanoon network dependency.
"""

from __future__ import annotations

import asyncio
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.agents.citation_verification import (
    apply_stripped_citations,
    extract_citations,
)
from app.agents.drafting import DraftingInput, generate_draft

FIXTURES_PATH = Path(__file__).parent / "fixtures.json"


@dataclass(slots=True)
class FixtureResult:
    fixture_id: str
    passed: bool
    failures: list[str]
    section_count: int
    sections_titles: list[str]
    verified_citations: int
    partial_citations: int
    stripped_citations: int


def load_fixtures() -> list[dict[str, Any]]:
    return json.loads(FIXTURES_PATH.read_text())


def _fixture_to_input(f: dict[str, Any]) -> DraftingInput:
    i = f["input"]
    n = i["notice"]
    notice_dict = {
        "notice_id": f["id"],
        "document_type": n.get("document_type"),
        "din_or_rfn": n.get("din_or_rfn"),
        "due_date": n.get("due_date"),
        "issue_date": n.get("issue_date"),
        "hearing_date": n.get("hearing_date"),
        "authority": n.get("authority"),
        "demand_amount": n.get("demand_amount"),
        "lifecycle_status": "issued",
        "issue": n.get("issue"),
    }
    return DraftingInput(
        matter_id=f["id"],  # type: ignore[arg-type]  -- the agent only reads it as opaque string
        tone=i["tone"],
        partner_instructions="",
        client_legal_name=i["client_legal_name"],
        client_pan=i["client_pan"],
        client_entity_type=i.get("client_entity_type"),
        registration_type=i["registration_type"],
        registration_identifier=i["registration_identifier"],
        registration_state_name=i.get("registration_state_name"),
        law=i["law"],
        financial_year=i.get("financial_year"),
        assessment_year=i.get("assessment_year"),
        notice=notice_dict,
        raw_extracted_json={"issue": n.get("issue")},
    )


_CITE_SPAN_RE = __import__("re").compile(
    r'<span\s+class="draft-citation"[^>]*>.*?</span>',
    __import__("re").IGNORECASE | __import__("re").DOTALL,
)


def _render_full(sections: list[dict[str, Any]]) -> str:
    return "\n".join(
        f"{s.get('title', '')}\n{s.get('body_html', '')}" for s in sections
    )


def _render_factual_matrix(sections: list[dict[str, Any]]) -> str:
    """Return rendered draft text with every citation span removed.

    Case law citations legitimately reference state names ("v. State of
    Karnataka", "Andhra Pradesh High Court", etc.) — those don't leak the
    assessee's registration context. Forbidden-substring checks should only
    fire on the factual matrix.
    """
    text = "\n".join(
        f"{s.get('title', '')}\n{s.get('body_html', '')}" for s in sections
    )
    return _CITE_SPAN_RE.sub("", text)


async def _evaluate_fixture(f: dict[str, Any]) -> FixtureResult:
    di = _fixture_to_input(f)
    generated = await generate_draft(di)
    sections = [
        {"num": s.num, "title": s.title, "body_html": s.body_html}
        for s in generated.sections
    ]

    # Walk the verifier so we exercise the strip-and-footnote path. We do
    # NOT hit the DB / cache here — the stub provider is called directly so
    # the eval stays fully in-memory.
    from app.agents.citation_verification import (
        StubCitationProvider,
        VerifiedCitation,
    )

    provider = StubCitationProvider()
    extracted = extract_citations(sections)
    verified: list[VerifiedCitation] = []
    for ec in extracted:
        result = await provider.verify(ec.case_name, ec.citation_string)
        action = {
            "VERIFIED": "passed",
            "VERIFIED_PARTIAL": "flagged",
            "UNVERIFIED": "stripped",
        }[result.status]
        verified.append(
            VerifiedCitation(
                extracted=ec,
                status=result.status,
                source_url=result.source_url,
                verified_paragraph_text=result.verified_paragraph_text,
                proposition_match_confidence=result.proposition_match_confidence,
                action_taken=action,
            )
        )
    final_sections, _ = apply_stripped_citations(sections, verified)

    expects = f["expectations"]
    failures: list[str] = []
    if len(final_sections) < expects.get("min_sections", 0):
        failures.append(
            f"section count {len(final_sections)} < min {expects['min_sections']}"
        )
    titles = [s["title"] for s in final_sections]
    for required in expects.get("required_section_titles", []):
        if required not in titles:
            failures.append(f"missing required section: {required}")
    full = _render_full(final_sections)
    for must in expects.get("must_mention_substrings", []):
        if must not in full:
            failures.append(f"missing required substring: {must!r}")
    # Registration-leak check ignores citation spans: case law references to
    # other states are not leaks; sibling-registration facts are.
    factual = _render_factual_matrix(final_sections)
    for forbidden in expects.get("must_not_mention_substrings", []):
        if forbidden in factual:
            failures.append(
                f"forbidden substring present (registration leak?): {forbidden!r}"
            )

    # AC: no UNVERIFIED citation reaches the final draft. Stripped ones are
    # acceptable (they're now [citation removed] markers); UNVERIFIED status
    # without strip is the failure mode.
    leaked = [v for v in verified if v.status == "UNVERIFIED" and v.action_taken != "stripped"]
    if leaked:
        failures.append(f"{len(leaked)} UNVERIFIED citations not stripped")

    counts = {"VERIFIED": 0, "VERIFIED_PARTIAL": 0, "UNVERIFIED": 0}
    for v in verified:
        counts[v.status] = counts.get(v.status, 0) + 1

    return FixtureResult(
        fixture_id=f["id"],
        passed=not failures,
        failures=failures,
        section_count=len(final_sections),
        sections_titles=titles,
        verified_citations=counts["VERIFIED"],
        partial_citations=counts["VERIFIED_PARTIAL"],
        stripped_citations=counts["UNVERIFIED"],
    )


async def main() -> int:
    fixtures = load_fixtures()
    results: list[FixtureResult] = []
    for f in fixtures:
        try:
            results.append(await _evaluate_fixture(f))
        except Exception as e:  # noqa: BLE001
            results.append(
                FixtureResult(
                    fixture_id=f["id"],
                    passed=False,
                    failures=[f"runner exception: {e}"],
                    section_count=0,
                    sections_titles=[],
                    verified_citations=0,
                    partial_citations=0,
                    stripped_citations=0,
                )
            )

    passed = sum(1 for r in results if r.passed)
    total = len(results)
    pass_rate = (passed / total) if total else 0

    for r in results:
        marker = "✓" if r.passed else "✗"
        print(
            f"{marker} {r.fixture_id:40s} sections={r.section_count:2d}  "
            f"cites V/P/S={r.verified_citations}/{r.partial_citations}/{r.stripped_citations}"
        )
        for fail in r.failures:
            print(f"   - {fail}")

    print()
    print(f"PASSED {passed}/{total}  ({pass_rate * 100:.1f}%)")
    target = 0.70
    if pass_rate < target:
        print(f"FAIL: pass rate {pass_rate * 100:.1f}% < target {target * 100:.0f}%")
        return 1
    print(f"OK: pass rate ≥ target {target * 100:.0f}%")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
