"""Vendor-abstracted outbound email.

Mirrors the storage / OCR / LLM service pattern: a thin
:class:`EmailProvider` interface with SMTP (universal — Gmail / Mailtrap /
SES-SMTP / any provider) and stub (writes to disk for tests + offline dev)
implementations behind a factory keyed off ``EMAIL_PROVIDER``.

The inbound side (SES → /v1/email/inbound) lives in routes/email.py;
this package is outbound-only.
"""

from app.services.email.base import (
    EmailError,
    EmailMessage,
    EmailProvider,
    EmailTransientError,
)
from app.services.email.factory import get_email_provider

__all__ = [
    "EmailError",
    "EmailMessage",
    "EmailProvider",
    "EmailTransientError",
    "get_email_provider",
]
