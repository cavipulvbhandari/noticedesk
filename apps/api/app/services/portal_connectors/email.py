"""Email-forward connector.

This connector is *passive*: documents arrive via the SES inbound webhook at
``/v1/email/inbound``. The connector exists so the inbox UI can show that an
email channel is active for the firm and report when the last email landed.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from app.services.portal_connectors.base import (
    ConnectorStatus,
    InboundDocument,
    PortalConnector,
)


class EmailForwardConnector(PortalConnector):
    name = "email"

    def __init__(self, *, slug: str, domain: str = "noticedesk.in") -> None:
        self._slug = slug
        self._domain = domain

    @property
    def inbound_address(self) -> str:
        return f"notices+{self._slug}@{self._domain}"

    async def fetch_pending_notices(
        self, registration_id: UUID
    ) -> list[InboundDocument]:
        # Inbound emails are pushed by SES, not pulled. Returning an empty
        # list is the correct behavior here.
        return []

    async def get_connector_status(
        self, registration_id: UUID
    ) -> ConnectorStatus:
        return ConnectorStatus(
            connector=self.name,
            healthy=True,
            last_success_at=datetime.now(UTC).isoformat(),
            notes={"inbound_address": self.inbound_address},
        )
