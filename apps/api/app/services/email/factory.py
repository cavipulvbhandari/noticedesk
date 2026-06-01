"""Email-provider factory.

Picks the provider keyed off ``EMAIL_PROVIDER`` and caches the instance.
Falls back cleanly to the stub if no provider is configured so dev /
CI / first-run experiences don't crash on a missing SMTP_HOST.
"""

from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.services.email.base import EmailError, EmailProvider
from app.services.email.smtp import SMTPEmailProvider
from app.services.email.stub import StubEmailProvider

KNOWN_EMAIL_PROVIDERS: frozenset[str] = frozenset({"smtp", "stub"})


@lru_cache(maxsize=1)
def get_email_provider() -> EmailProvider:
    s = get_settings()
    name = (s.email_provider or "stub").lower()
    if name == "smtp":
        return SMTPEmailProvider(
            host=s.smtp_host or "",
            port=s.smtp_port or 587,
            username=s.smtp_username,
            password=s.smtp_password,
            use_tls=s.smtp_use_tls,
        )
    if name == "stub":
        return StubEmailProvider(output_dir=s.email_stub_dir)
    raise EmailError(
        f"unknown EMAIL_PROVIDER {name!r}; valid: {sorted(KNOWN_EMAIL_PROVIDERS)}"
    )
