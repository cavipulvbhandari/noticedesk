"""Auth verification.

Sprint 1 supports two providers, switched by AUTH_PROVIDER:

- ``clerk``: verify a JWT against Clerk's JWKS. Claims are expected to include
  ``sub`` (user id) and a custom ``tenant_id`` claim populated via Clerk's
  organization metadata.
- ``dev``: development bypass that trusts ``X-Dev-User-Id`` and
  ``X-Dev-Tenant-Id`` headers. Rejected unless ENVIRONMENT=development.

The verifier returns an :class:`AuthClaims` object; tenant resolution and
session loading happen in middleware downstream.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request

from app.core.config import Settings, get_settings
from app.core.errors import AuthError


@dataclass(frozen=True, slots=True)
class AuthClaims:
    user_id: str
    tenant_id: str
    email: str | None = None


class AuthVerifier:
    """Pluggable auth verifier."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def verify(self, request: Request) -> AuthClaims:
        if self._settings.auth_provider == "dev":
            return self._verify_dev(request)
        return await self._verify_clerk(request)

    def _verify_dev(self, request: Request) -> AuthClaims:
        if not self._settings.is_dev_auth_allowed:
            raise AuthError("dev auth bypass is not allowed in this environment")
        user_id = request.headers.get("x-dev-user-id")
        tenant_id = request.headers.get("x-dev-tenant-id")
        if not user_id or not tenant_id:
            raise AuthError("missing X-Dev-User-Id or X-Dev-Tenant-Id headers")
        return AuthClaims(user_id=user_id, tenant_id=tenant_id)

    async def _verify_clerk(self, request: Request) -> AuthClaims:
        # Sprint 1 stub: real Clerk JWKS verification is wired in once the
        # tenant has chosen Clerk vs Auth0 (decision pending India-region
        # availability check).
        token = _extract_bearer(request)
        if not token:
            raise AuthError("missing bearer token")
        # V2 candidate: full JWKS-based JWT verification with caching.
        raise AuthError("clerk auth verification is not yet implemented")


def _extract_bearer(request: Request) -> str | None:
    header = request.headers.get("authorization") or request.headers.get("Authorization")
    if not header:
        return None
    parts = header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip() or None
