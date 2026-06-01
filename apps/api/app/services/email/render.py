"""Email template rendering.

Keeps the templating intentionally simple — Python ``str.format_map`` with a
dict-with-missing-fallback so a forgotten placeholder renders as ``—``
instead of throwing. If we grow past ~5 templates with substantial logic,
switch to Jinja2.

All templates live under ``services/email/templates/`` and are addressed by
their basename (``checklist`` resolves to both ``checklist.html`` and
``checklist.txt``).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

TEMPLATES_DIR = Path(__file__).parent / "templates"


class _SafeDict(dict[str, Any]):
    """dict that returns '—' for missing keys instead of raising KeyError."""

    def __missing__(self, key: str) -> str:  # noqa: ARG002 — key unused
        return "—"


def render(template_name: str, variables: dict[str, Any]) -> tuple[str, str]:
    """Return (body_text, body_html) for the named template.

    Raises FileNotFoundError if neither .txt nor .html exists.
    """
    txt_path = TEMPLATES_DIR / f"{template_name}.txt"
    html_path = TEMPLATES_DIR / f"{template_name}.html"
    if not txt_path.exists():
        raise FileNotFoundError(f"missing template: {txt_path}")
    safe = _SafeDict(variables)
    body_text = txt_path.read_text(encoding="utf-8").format_map(safe)
    body_html = (
        html_path.read_text(encoding="utf-8").format_map(safe)
        if html_path.exists()
        else ""
    )
    return body_text, body_html
