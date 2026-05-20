"""GST Appellate Authority prompt artifacts (Section 107, CGST Act, 2017).

Two prompts ship in this package:

- ``mock_personal_hearing.md`` — live, turn-by-turn quasi-judicial persona.
- ``post_hearing_critique.md``  — one-shot structured critique that runs
  after a hearing transcript has been captured.

Both are loaded as raw Markdown by
:func:`noticedesk_agents.prompts.render.load_prompt`.
"""

from __future__ import annotations

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent

MOCK_PERSONAL_HEARING = PROMPTS_DIR / "mock_personal_hearing.md"
POST_HEARING_CRITIQUE = PROMPTS_DIR / "post_hearing_critique.md"

__all__ = ["PROMPTS_DIR", "MOCK_PERSONAL_HEARING", "POST_HEARING_CRITIQUE"]
