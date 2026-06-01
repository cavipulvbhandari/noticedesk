"""Email provider contract."""

from __future__ import annotations

import abc
from dataclasses import dataclass


class EmailError(Exception):
    """Permanent email send failure that will not improve on retry
    (bad address format, auth, etc.)."""


class EmailTransientError(EmailError):
    """Temporary failure (timeout, 4xx rate-limit, 5xx) — safe to retry."""


@dataclass(frozen=True, slots=True)
class EmailMessage:
    """A single outbound email. The provider renders this to the wire
    format (RFC 2822 MIME for SMTP, JSON for SES API, etc.)."""

    to: tuple[str, ...]
    subject: str
    body_text: str
    body_html: str | None = None
    from_address: str = ""  # filled by factory from settings if blank
    from_name: str = ""     # filled by factory from settings if blank
    reply_to: str | None = None
    # Optional per-tenant correlation tag the audit log can key off.
    tag: str = ""


class EmailProvider(abc.ABC):
    """Async email provider interface."""

    name: str

    @abc.abstractmethod
    async def send(self, message: EmailMessage) -> str:
        """Send one message; returns the provider's message-id when known.

        Implementations should raise :class:`EmailTransientError` for
        retryable failures and :class:`EmailError` for permanent ones.
        """
