"""Minimal `{{VAR}}` renderer for NoticeDesk prompt templates.

The renderer is deliberately tiny: no Jinja, no f-string evaluation, no
shelling out — just literal substitution. The template language is
``{{NAME}}`` where ``NAME`` matches ``[A-Z_][A-Z0-9_]*``. Anything that
does not match is left alone, which keeps the Markdown's own braces and
code blocks safe.

Empty or whitespace values, and the literal token ``__MISSING__``, are
preserved as the sentinel ``__MISSING__`` in the rendered output so the
prompt's empty-variable rules can fire deterministically downstream.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping

PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Z_][A-Z0-9_]*)\s*\}\}")
MISSING_SENTINEL = "__MISSING__"


class TemplateError(ValueError):
    """Raised when a template cannot be rendered safely."""


@dataclass(frozen=True)
class RenderResult:
    text: str
    substituted: tuple[str, ...]
    missing: tuple[str, ...] = field(default=())

    @property
    def is_clean(self) -> bool:
        """True when every placeholder discovered in the template was filled."""
        return not self.missing


def find_placeholders(template: str) -> list[str]:
    """Return every distinct placeholder name appearing in *template*, in order."""
    seen: list[str] = []
    for match in PLACEHOLDER_RE.finditer(template):
        name = match.group(1)
        if name not in seen:
            seen.append(name)
    return seen


def _coerce(value: object) -> str:
    if value is None:
        return MISSING_SENTINEL
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped or stripped == MISSING_SENTINEL:
            return MISSING_SENTINEL
        return value
    return str(value)


def render(
    template: str,
    variables: Mapping[str, object],
    *,
    required: Iterable[str] = (),
) -> RenderResult:
    """Substitute ``{{VAR}}`` placeholders in *template* using *variables*.

    Parameters
    ----------
    template:
        The raw prompt template text.
    variables:
        Mapping of placeholder name -> value. Strings are used verbatim;
        ``None``, ``""`` and ``__MISSING__`` collapse to the missing
        sentinel. Other types are coerced via :class:`str`.
    required:
        Names that must be supplied with a non-missing value. A
        :class:`TemplateError` is raised if any required placeholder is
        absent from *variables* or collapses to the missing sentinel.

    Returns
    -------
    RenderResult
        ``text`` is the rendered template, ``substituted`` lists the
        placeholders that were filled with real values, and ``missing``
        lists the ones that fell through to the sentinel.
    """

    coerced: dict[str, str] = {
        name: _coerce(value) for name, value in variables.items()
    }

    required_set = set(required)
    missing_required = sorted(
        name
        for name in required_set
        if coerced.get(name, MISSING_SENTINEL) == MISSING_SENTINEL
    )
    if missing_required:
        raise TemplateError(
            "missing required variables: " + ", ".join(missing_required)
        )

    substituted: list[str] = []
    missing: list[str] = []

    def _replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name in coerced:
            value = coerced[name]
            if value == MISSING_SENTINEL:
                if name not in missing:
                    missing.append(name)
            else:
                if name not in substituted:
                    substituted.append(name)
            return value
        if name not in missing:
            missing.append(name)
        return MISSING_SENTINEL

    rendered = PLACEHOLDER_RE.sub(_replace, template)
    return RenderResult(
        text=rendered,
        substituted=tuple(substituted),
        missing=tuple(missing),
    )


def load_prompt(path: Path | str) -> str:
    """Read a prompt file from disk as UTF-8 text."""
    return Path(path).read_text(encoding="utf-8")
