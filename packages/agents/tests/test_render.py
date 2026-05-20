"""Tests for the prompt renderer.

These tests cover only the substitution helper; structural and
scenario-level checks on the GST appellate prompts live in
``test_gst_appellate_prompts.py``.
"""

from __future__ import annotations

import pytest

from noticedesk_agents.prompts.render import (
    MISSING_SENTINEL,
    TemplateError,
    find_placeholders,
    render,
)


def test_find_placeholders_returns_unique_names_in_order():
    template = "{{A}} then {{B}} then {{A}} and {{C}}"
    assert find_placeholders(template) == ["A", "B", "C"]


def test_render_substitutes_known_variables():
    result = render("Hello {{NAME}}", {"NAME": "Counsel"})
    assert result.text == "Hello Counsel"
    assert result.substituted == ("NAME",)
    assert result.missing == ()
    assert result.is_clean is True


def test_render_marks_empty_strings_as_missing():
    result = render(
        "OIO: {{OIO_TEXT}} | GoA: {{GOA_TEXT}}",
        {"OIO_TEXT": "  ", "GOA_TEXT": "ground 1"},
    )
    assert MISSING_SENTINEL in result.text
    assert "OIO_TEXT" in result.missing
    assert "GOA_TEXT" in result.substituted
    assert result.is_clean is False


def test_render_treats_sentinel_token_as_missing():
    result = render("{{X}}", {"X": MISSING_SENTINEL})
    assert result.text == MISSING_SENTINEL
    assert result.missing == ("X",)


def test_render_handles_none_as_missing():
    result = render("{{X}}", {"X": None})
    assert result.text == MISSING_SENTINEL
    assert result.missing == ("X",)


def test_render_falls_through_unknown_placeholders_to_sentinel():
    result = render("Hi {{UNKNOWN}}", {})
    assert result.text == f"Hi {MISSING_SENTINEL}"
    assert result.missing == ("UNKNOWN",)


def test_render_required_missing_raises():
    with pytest.raises(TemplateError) as exc:
        render(
            "{{A}} {{B}}",
            {"A": "ok", "B": ""},
            required=("A", "B"),
        )
    assert "B" in str(exc.value)


def test_render_required_present_passes():
    result = render(
        "{{A}} {{B}}",
        {"A": "ok", "B": "fine"},
        required=("A", "B"),
    )
    assert result.is_clean
    assert result.substituted == ("A", "B")


def test_render_ignores_non_placeholder_braces():
    # The Markdown prompts contain code fences with literal braces — make
    # sure the renderer leaves those alone.
    template = "```\n{ not_a_placeholder }\n```\n{{REAL}}"
    result = render(template, {"REAL": "value"})
    assert "{ not_a_placeholder }" in result.text
    assert "value" in result.text


def test_render_coerces_non_string_values():
    result = render("count: {{N}}", {"N": 42})
    assert result.text == "count: 42"
    assert result.substituted == ("N",)
