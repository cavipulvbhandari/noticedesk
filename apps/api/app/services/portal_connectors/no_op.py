"""No-op connector for registrations without an active inbound channel."""

from __future__ import annotations

from uuid import UUID

from app.services.portal_connectors.base import (
    ConnectorStatus,
    InboundDocument,
    PortalConnector,
)


class NoOpConnector(PortalConnector):
    """Returns no documents and reports healthy.

    Used as the default connector for any registration that doesn't have an
    explicit one configured. It is intentionally inert — the inbox UI shows
    such registrations with a "no connector configured" hint sourced from
    :meth:`get_connector_status`.
    """

    name = "no_op"

    async def fetch_pending_notices(
        self, registration_id: UUID
    ) -> list[InboundDocument]:
        return []

    async def get_connector_status(
        self, registration_id: UUID
    ) -> ConnectorStatus:
        return ConnectorStatus(
            connector=self.name,
            healthy=True,
            notes={"message": "no connector configured for this registration"},
        )
