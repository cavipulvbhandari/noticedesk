"""Prompt artifacts and a small renderer for the NoticeDesk agent prompts.

Prompts are plain Markdown with `{{VARIABLE}}` placeholders. The renderer
in :mod:`noticedesk_agents.prompts.render` performs strict substitution
and surfaces missing placeholders so callers can decide whether to block
or proceed.
"""

from __future__ import annotations

__all__: list[str] = []
