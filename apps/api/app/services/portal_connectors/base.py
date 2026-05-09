"""Inbound-notice connector contract."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

IngestChannel = str  # narrowed by the documents_inbox.ingest_channel CHECK


@dataclass(frozen=True, slots=True)
class InboundDocument:
    """A document that arrived from an inbound channel.

    The connector hands these to the upload pipeline; the pipeline computes
    the SHA-256, persists to storage, and creates the documents_inbox row.
    """

    filename: str
    content: bytes
    mime_type: str
    ingest_channel: IngestChannel
    ingest_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ConnectorStatus:
    """Operational status of a connector for a given registration.

    For Sprint 2 this is informational only; downstream sprints surface it on
    the registration screen so partners can see why a portal isn't pulling.
    """

    connector: str
    healthy: bool
    last_success_at: str | None = None
    last_error: str | None = None
    notes: dict[str, Any] = field(default_factory=dict)


class PortalConnector(abc.ABC):
    """Inbound-notice connector base class.

    Sprint 2 implementations:

    - :class:`NoOpConnector` — placeholder for registrations without a
      configured connector.
    - :class:`EmailForwardConnector` — passive; documents arrive via the
      ``/v1/email/inbound`` webhook and this connector simply reports health.

    Future implementations (NOT in Sprint 2):

    - ``GSPConnector`` — pulls notices from the GST portal via a GSP partner.
      V2 candidate.
    - ``ITPortalAAConnector`` — pulls Income Tax notices via Account
      Aggregator. V2 candidate.
    """

    name: str

    @abc.abstractmethod
    async def fetch_pending_notices(
        self, registration_id: UUID
    ) -> list[InboundDocument]:
        ...

    @abc.abstractmethod
    async def get_connector_status(
        self, registration_id: UUID
    ) -> ConnectorStatus:
        ...
