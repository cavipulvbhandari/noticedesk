"""Structural and scenario-level checks for the GST Appellate prompts.

These tests do not invoke a real LLM. They verify that the prompt
artifacts on disk are well-formed, that the renderer fills them cleanly
against representative case-file scenarios, and that the hardening rules
expected by Section 3 / 10 of the mock PH prompt are actually present.

A separate LLM-driven eval (out of scope for this harness) can layer on
top to score live model output.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from noticedesk_agents.prompts.gst_appellate import (
    MOCK_PERSONAL_HEARING,
    POST_HEARING_CRITIQUE,
)
from noticedesk_agents.prompts.render import (
    MISSING_SENTINEL,
    find_placeholders,
    load_prompt,
    render,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "gst_appellate"

PERSONAS = {
    "strict_pro_revenue",
    "procedural_stickler",
    "fact_focused",
    "balanced",
}
DIFFICULTIES = {
    "light",
    "standard",
    "hostile",
    "technical_deep_dive",
}

MOCK_PH_REQUIRED = {
    "OIO_TEXT",
    "GOA_TEXT",
    "PREDEPOSIT_TEXT",
    "LIMITATION_TEXT",
    "PERSONA",
    "DIFFICULTY",
    "AR_NAME",
    "MATTER_TITLE",
    "APPEAL_NUMBER",
}
MOCK_PH_OPTIONAL = {
    "WS_TEXT",
    "EVIDENCE_INDEX",
    "CITED_AUTHORITIES",
    "MISC_ORDERS",
}

CRITIQUE_REQUIRED = {
    "PH_TRANSCRIPT",
    "PERSONA_USED",
    "DIFFICULTY_USED",
    "AR_NAME",
    "MATTER_TITLE",
    "APPEAL_NUMBER",
    "OIO_TEXT",
    "GOA_TEXT",
    "PREDEPOSIT_TEXT",
    "LIMITATION_TEXT",
}
CRITIQUE_OPTIONAL = {
    "WS_TEXT",
    "EVIDENCE_INDEX",
    "CITED_AUTHORITIES",
    "MISC_ORDERS",
}

MOCK_PH_REQUIRED_HEADINGS = [
    "## 1. ROLE & IDENTITY",
    "## 2. CASE FILE (GROUNDING — STRICT)",
    "## 3. ANTI-HALLUCINATION (NON-NEGOTIABLE)",
    "## 4. PERSONA PROFILE",
    "## 5. DIFFICULTY LEVEL",
    "## 6. SESSION STRUCTURE",
    "## 7. CONDUCT RULES",
    "## 8. OUTPUT FORMAT (PER TURN)",
    "## 9. CLOSING THE HEARING",
    "## 10. STAY-IN-ROLE & ROLE-BREAK REFUSAL",
    "## 11. SESSION TERMINATION",
    "## 12. VARIABLES (DEVELOPER-FACING)",
    "## 13. PRE-FLIGHT VALIDATION (BACKEND, BEFORE FIRING THIS PROMPT)",
]

CRITIQUE_REQUIRED_HEADINGS = [
    "## 1. ROLE & IDENTITY",
    "## 2. INPUTS",
    "## 3. ANTI-HALLUCINATION (NON-NEGOTIABLE)",
    "## 4. STAY-IN-ROLE",
    "## 5. OUTPUT FORMAT (THE REPORT)",
    "## 6. WHAT TO NEVER INCLUDE",
    "## 7. VARIABLES (DEVELOPER-FACING)",
]

TERMINATION_SEPARATOR = "--- END OF MOCK PERSONAL HEARING ---"
CLOSING_OPENER = "Heard the learned AR at length on all grounds."


# ---------------------------------------------------------------------------
# File-level sanity
# ---------------------------------------------------------------------------


def test_prompt_files_exist_and_are_substantive():
    for path in (MOCK_PERSONAL_HEARING, POST_HEARING_CRITIQUE):
        assert path.exists(), f"missing prompt file: {path}"
        text = load_prompt(path)
        assert len(text) > 3_000, f"prompt looks truncated: {path}"


# ---------------------------------------------------------------------------
# Mock PH prompt structure
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def mock_ph_text() -> str:
    return load_prompt(MOCK_PERSONAL_HEARING)


def test_mock_ph_has_required_headings(mock_ph_text: str):
    for heading in MOCK_PH_REQUIRED_HEADINGS:
        assert heading in mock_ph_text, f"missing heading: {heading}"


def test_mock_ph_mentions_every_persona(mock_ph_text: str):
    for persona in PERSONAS:
        assert persona in mock_ph_text, f"persona enum missing: {persona}"


def test_mock_ph_mentions_every_difficulty(mock_ph_text: str):
    for difficulty in DIFFICULTIES:
        assert difficulty in mock_ph_text, f"difficulty enum missing: {difficulty}"


def test_mock_ph_has_termination_separator(mock_ph_text: str):
    assert TERMINATION_SEPARATOR in mock_ph_text


def test_mock_ph_has_verbatim_closing_string(mock_ph_text: str):
    assert CLOSING_OPENER in mock_ph_text


def test_mock_ph_anti_hallucination_rules_present(mock_ph_text: str):
    # The Section 3 hardening must be present in spirit, not just header.
    must_have = [
        "Zero tolerance",
        "must not",
        "Invent case names",
        "CBIC Circulars",
        "Refusal template",
    ]
    for phrase in must_have:
        assert phrase in mock_ph_text, f"anti-hallucination phrase missing: {phrase}"


def test_mock_ph_role_break_refusal_present(mock_ph_text: str):
    assert "decline in character" in mock_ph_text
    assert "matter for after the order" in mock_ph_text


def test_mock_ph_placeholders_are_all_documented(mock_ph_text: str):
    placeholders = find_placeholders(mock_ph_text)
    assert placeholders, "expected non-empty placeholder list"
    table_section = mock_ph_text.split("## 12. VARIABLES")[1].split("## 13.")[0]
    for name in placeholders:
        assert (
            f"`{{{{{name}}}}}`" in table_section
        ), f"placeholder {name} not documented in variables table"


def test_mock_ph_required_and_optional_split_matches_intent(mock_ph_text: str):
    placeholders = set(find_placeholders(mock_ph_text))
    # Every required + optional variable we expect must actually appear in
    # the prompt — otherwise the table and the body have drifted.
    expected = MOCK_PH_REQUIRED | MOCK_PH_OPTIONAL
    missing = expected - placeholders
    assert not missing, f"prompt body is missing declared variables: {missing}"


# ---------------------------------------------------------------------------
# Critique prompt structure
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def critique_text() -> str:
    return load_prompt(POST_HEARING_CRITIQUE)


def test_critique_has_required_headings(critique_text: str):
    for heading in CRITIQUE_REQUIRED_HEADINGS:
        assert heading in critique_text, f"missing heading: {heading}"


def test_critique_is_not_a_live_module(critique_text: str):
    # The critique prompt may *reference* the hearing's termination
    # separator (as a parse marker for the incoming transcript) but must
    # never emit it on its own line — that would let a transcript parser
    # mistake the critique output for hearing output.
    for line in critique_text.splitlines():
        assert line.strip() != TERMINATION_SEPARATOR, (
            "critique must not emit the hearing termination separator standalone"
        )


def test_critique_refuses_outcome_prediction(critique_text: str):
    must_have = [
        "do not predict",
        "Do not predict outcomes",
    ]
    lowered = critique_text.lower()
    assert any(phrase.lower() in lowered for phrase in must_have)


def test_critique_anti_hallucination_rules_present(critique_text: str):
    for phrase in ("Zero tolerance", "must not", "Invent case names"):
        assert phrase in critique_text


def test_critique_placeholders_are_all_documented(critique_text: str):
    placeholders = find_placeholders(critique_text)
    assert placeholders
    table_section = critique_text.split("## 7. VARIABLES")[1]
    for name in placeholders:
        assert (
            f"`{{{{{name}}}}}`" in table_section
        ), f"placeholder {name} not documented in variables table"


def test_critique_carries_transcript_input(critique_text: str):
    assert "{{PH_TRANSCRIPT}}" in critique_text


# ---------------------------------------------------------------------------
# Fixture-driven rendering: mock PH
# ---------------------------------------------------------------------------


FIXTURES = ("thin_file", "limitation_defect", "strong_merits")


def _load_fixture(name: str) -> dict:
    path = FIXTURE_DIR / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("scenario", FIXTURES)
def test_fixture_renders_mock_ph_cleanly_for_required_vars(
    scenario: str, mock_ph_text: str
):
    fixture = _load_fixture(scenario)
    variables = fixture["variables"]

    result = render(
        mock_ph_text,
        variables,
        required=tuple(MOCK_PH_REQUIRED),
    )

    # Anything still missing must be an *optional* variable.
    leftover_required = set(result.missing) & MOCK_PH_REQUIRED
    assert not leftover_required, f"required vars unfilled: {leftover_required}"


@pytest.mark.parametrize("scenario", FIXTURES)
def test_fixture_persona_and_difficulty_round_trip(scenario: str, mock_ph_text: str):
    fixture = _load_fixture(scenario)
    variables = fixture["variables"]
    persona = variables["PERSONA"]
    difficulty = variables["DIFFICULTY"]
    assert persona in PERSONAS
    assert difficulty in DIFFICULTIES

    result = render(mock_ph_text, variables, required=tuple(MOCK_PH_REQUIRED))
    # The rendered case-file XML block should carry the persona/difficulty
    # values via the placeholders — confirm they survived substitution.
    assert persona in result.text
    assert difficulty in result.text


def test_thin_file_optional_fields_collapse_to_sentinel(mock_ph_text: str):
    fixture = _load_fixture("thin_file")
    result = render(
        mock_ph_text,
        fixture["variables"],
        required=tuple(MOCK_PH_REQUIRED),
    )
    # The thin-file scenario deliberately leaves four optional fields empty.
    for name in ("WS_TEXT", "EVIDENCE_INDEX", "CITED_AUTHORITIES", "MISC_ORDERS"):
        assert name in result.missing, f"{name} should have collapsed to sentinel"
    # And the sentinel should actually appear in the rendered output.
    assert MISSING_SENTINEL in result.text


def test_limitation_defect_surfaces_time_bar(mock_ph_text: str):
    fixture = _load_fixture("limitation_defect")
    result = render(
        mock_ph_text,
        fixture["variables"],
        required=tuple(MOCK_PH_REQUIRED),
    )
    # The limitation summary must be visible inside the rendered case file,
    # so the bench can probe it. If this fails, the variable did not land in
    # the body where it was supposed to.
    assert "beyond three months" in result.text
    assert "21 March 2025" in result.text
    assert "procedural_stickler" in result.text


def test_strong_merits_includes_cited_authorities(mock_ph_text: str):
    fixture = _load_fixture("strong_merits")
    result = render(
        mock_ph_text,
        fixture["variables"],
        required=tuple(MOCK_PH_REQUIRED),
    )
    assert "Circular No. 199/11/2023-GST" in result.text
    # Hostile persona + hostile difficulty must both round-trip.
    assert result.text.count("hostile") >= 2


# ---------------------------------------------------------------------------
# Fixture-driven rendering: critique
# ---------------------------------------------------------------------------


def _critique_variables_from(fixture: dict, *, transcript: str) -> dict:
    """Adapt a hearing fixture into a critique-input bundle."""
    src = fixture["variables"]
    return {
        "PH_TRANSCRIPT": transcript,
        "PERSONA_USED": src["PERSONA"],
        "DIFFICULTY_USED": src["DIFFICULTY"],
        "AR_NAME": src["AR_NAME"],
        "MATTER_TITLE": src["MATTER_TITLE"],
        "APPEAL_NUMBER": src["APPEAL_NUMBER"],
        "OIO_TEXT": src["OIO_TEXT"],
        "GOA_TEXT": src["GOA_TEXT"],
        "WS_TEXT": src.get("WS_TEXT", ""),
        "EVIDENCE_INDEX": src.get("EVIDENCE_INDEX", ""),
        "CITED_AUTHORITIES": src.get("CITED_AUTHORITIES", ""),
        "PREDEPOSIT_TEXT": src["PREDEPOSIT_TEXT"],
        "LIMITATION_TEXT": src["LIMITATION_TEXT"],
        "MISC_ORDERS": src.get("MISC_ORDERS", ""),
    }


SAMPLE_TRANSCRIPT = """\
Bench (Turn 1): Counsel, kindly introduce the appeal.
AR (Turn 2): Thank you, Sir. This appeal is against OIO confirming demand for FY 2022-23.
Bench (Turn 3): I shall take up procedural compliance first. Kindly address me on pre-deposit.
AR (Turn 4): Pre-deposit of 10% was paid by DRC-03 dated 02 February 2025.
Bench (Turn 5): Noted. Kindly take me to Ground 1 of your appeal.
--- END OF MOCK PERSONAL HEARING ---
"""


@pytest.mark.parametrize("scenario", FIXTURES)
def test_fixture_renders_critique_cleanly_for_required_vars(
    scenario: str, critique_text: str
):
    fixture = _load_fixture(scenario)
    variables = _critique_variables_from(fixture, transcript=SAMPLE_TRANSCRIPT)
    result = render(
        critique_text,
        variables,
        required=tuple(CRITIQUE_REQUIRED),
    )
    leftover_required = set(result.missing) & CRITIQUE_REQUIRED
    assert not leftover_required, f"required vars unfilled: {leftover_required}"
    assert SAMPLE_TRANSCRIPT.strip().splitlines()[0] in result.text


def test_critique_required_vars_enforced(critique_text: str):
    fixture = _load_fixture("thin_file")
    variables = _critique_variables_from(fixture, transcript="")
    # An empty transcript must trip the required-vars guard.
    from noticedesk_agents.prompts.render import TemplateError

    with pytest.raises(TemplateError) as exc:
        render(
            critique_text,
            variables,
            required=tuple(CRITIQUE_REQUIRED),
        )
    assert "PH_TRANSCRIPT" in str(exc.value)
