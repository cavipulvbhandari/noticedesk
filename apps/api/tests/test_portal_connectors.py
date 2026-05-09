"""PortalConnector contract tests.

Sprint 2 ships only the no-op connector and the email-forward connector.
GSPConnector and ITPortalAAConnector are intentionally absent — see
``services/portal_connectors/base.py`` for the V2 placeholder.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.services.portal_connectors import (
    EmailForwardConnector,
    NoOpConnector,
    PortalConnector,
)


@pytest.mark.asyncio
async def test_no_op_returns_no_documents() -> None:
    c = NoOpConnector()
    assert isinstance(c, PortalConnector)
    assert c.name == "no_op"
    docs = await c.fetch_pending_notices(uuid4())
    assert docs == []
    status = await c.get_connector_status(uuid4())
    assert status.healthy is True
    assert status.connector == "no_op"


@pytest.mark.asyncio
async def test_email_forward_inbound_address() -> None:
    c = EmailForwardConnector(slug="mehta-associates")
    assert c.inbound_address == "notices+mehta-associates@noticedesk.in"
    docs = await c.fetch_pending_notices(uuid4())
    assert docs == []  # passive connector
    status = await c.get_connector_status(uuid4())
    assert status.healthy is True
    assert status.notes["inbound_address"] == "notices+mehta-associates@noticedesk.in"


def test_gsp_and_aa_connectors_not_implemented() -> None:
    """Sprint 2 must not ship these. If this test fails, scope has crept."""
    from app.services import portal_connectors as mod

    # Public re-exports list. Only no-op and email connectors ship in Sprint 2.
    assert "GSPConnector" not in mod.__all__
    assert "ITPortalAAConnector" not in mod.__all__
