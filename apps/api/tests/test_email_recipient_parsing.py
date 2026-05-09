"""Email recipient → tenant slug parsing."""

from __future__ import annotations

import pytest

from app.routes.email import _extract_slug


@pytest.mark.parametrize(
    ("recipient", "expected"),
    [
        ("notices+mehta-associates@noticedesk.in", "mehta-associates"),
        ("Notices+Foo-Firm@noticedesk.in", "foo-firm"),
        ("  notices+abc@noticedesk.in  ", "abc"),
    ],
)
def test_valid_recipient(recipient: str, expected: str) -> None:
    assert _extract_slug(recipient, "noticedesk.in") == expected


@pytest.mark.parametrize(
    "recipient",
    [
        "",
        "notices@noticedesk.in",  # no slug
        "support+abc@noticedesk.in",  # wrong local part
        "notices+abc@example.com",  # wrong domain
        "notices+UPPER_CASE@noticedesk.in",  # bad slug chars
    ],
)
def test_invalid_recipient(recipient: str) -> None:
    assert _extract_slug(recipient, "noticedesk.in") is None
