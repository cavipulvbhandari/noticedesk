"""Pluggable inbound notice connectors.

Each connector pulls (or receives) notices for a specific channel and yields
:class:`InboundDocument` records that the upload pipeline can then OCR. Sprint 2
ships only the no-op connector and the email-forward connector hook. The GST
GSP and IT portal/AA connectors are planned but **not** implemented in this
sprint — see ``base.py`` for the contract they will satisfy.
"""

from app.services.portal_connectors.base import (
    ConnectorStatus,
    InboundDocument,
    PortalConnector,
)
from app.services.portal_connectors.email import EmailForwardConnector
from app.services.portal_connectors.no_op import NoOpConnector

__all__ = [
    "ConnectorStatus",
    "EmailForwardConnector",
    "InboundDocument",
    "NoOpConnector",
    "PortalConnector",
]
