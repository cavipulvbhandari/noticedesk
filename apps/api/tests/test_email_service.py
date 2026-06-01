"""Outbound email service — stub, factory, render."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.email import EmailMessage, get_email_provider
from app.services.email.render import render
from app.services.email.stub import StubEmailProvider


@pytest.mark.asyncio
async def test_stub_writes_metadata_and_body(tmp_path: Path) -> None:
    provider = StubEmailProvider(output_dir=str(tmp_path))
    message = EmailMessage(
        to=("acme@example.com",),
        subject="Docs needed for ASMT-10",
        body_text="Plain text body",
        body_html="<p>HTML body</p>",
        from_address="noreply@noticedesk.in",
        from_name="NoticeDesk",
        tag="checklist:abc",
    )
    message_id = await provider.send(message)

    assert message_id, "stub should return a non-empty message-id"
    json_files = list(tmp_path.glob("*.json"))
    html_files = list(tmp_path.glob("*.html"))
    assert len(json_files) == 1
    assert len(html_files) == 1

    meta = json.loads(json_files[0].read_text())
    assert meta["to"] == ["acme@example.com"]
    assert meta["subject"] == "Docs needed for ASMT-10"
    assert meta["tag"] == "checklist:abc"
    assert "noticedesk" in meta["from"].lower()
    assert html_files[0].read_text() == "<p>HTML body</p>"


@pytest.mark.asyncio
async def test_stub_handles_html_absent(tmp_path: Path) -> None:
    provider = StubEmailProvider(output_dir=str(tmp_path))
    message = EmailMessage(
        to=("acme@example.com",),
        subject="text-only",
        body_text="line",
        from_address="noreply@noticedesk.in",
    )
    await provider.send(message)
    html = next(tmp_path.glob("*.html")).read_text()
    # text-only body should still render in the .html with a <pre> wrapper.
    assert "<pre>" in html and "line" in html


def test_factory_returns_stub_by_default(monkeypatch, tmp_path: Path) -> None:
    from app.services.email import factory as email_factory
    from app.core.config import Settings

    monkeypatch.setattr(
        email_factory,
        "get_settings",
        lambda: Settings(email_provider="stub", email_stub_dir=str(tmp_path)),
    )
    email_factory.get_email_provider.cache_clear()
    provider = email_factory.get_email_provider()
    assert provider.name == "stub"


def test_factory_returns_smtp_when_configured(monkeypatch) -> None:
    from app.services.email import factory as email_factory
    from app.core.config import Settings

    monkeypatch.setattr(
        email_factory,
        "get_settings",
        lambda: Settings(
            email_provider="smtp",
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_username="u",
            smtp_password="p",
        ),
    )
    email_factory.get_email_provider.cache_clear()
    provider = email_factory.get_email_provider()
    assert provider.name == "smtp"


def test_render_substitutes_variables() -> None:
    body_text, body_html = render(
        "checklist",
        {
            "firm_name": "Acme & Co",
            "client_legal_name": "Beta Industries",
            "notice_type_label": "ASMT-10",
            "notice_number": "DIN123",
            "authority": "STO Pune",
            "issue_date": "2026-04-15",
            "due_date": "2026-05-15",
            "registration_label": "GST 27AAAAA0000A1Z5 (MH)",
            "summary": "Officer alleges ITC mismatch.",
            "checklist_html": "<ol><li>GSTR-3B</li></ol>",
            "checklist_text": "1. GSTR-3B",
            "sent_at": "01 Jun 2026, 09:00 UTC",
        },
    )
    assert "Acme & Co" in body_text and "Acme & Co" in body_html
    assert "Beta Industries" in body_text
    assert "ASMT-10" in body_text
    assert "GSTR-3B" in body_text
    assert "<ol>" in body_html


def test_render_falls_back_to_em_dash_for_missing_keys() -> None:
    body_text, _ = render(
        "checklist",
        {
            "firm_name": "Firm",
            "client_legal_name": "Client",
        },
    )
    # Missing keys ('notice_number', 'authority', etc.) render as em-dash
    # rather than throwing — a forgotten variable degrades, not crashes.
    assert "—" in body_text
