"""Tenant context dependency.

Every authenticated request must run ``SET LOCAL app.current_tenant`` on the
session before issuing tenant-scoped queries. Without it, RLS policies hide
every row.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AuthClaims, AuthVerifier
from app.core.db import get_session
from app.core.errors import AuthError


@dataclass(frozen=True, slots=True)
class RequestContext:
    """Per-request identity + a session bound to the current tenant."""

    claims: AuthClaims
    session: AsyncSession


async def request_context(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RequestContext:
    verifier = AuthVerifier()
    claims = await verifier.verify(request)

    if not claims.tenant_id or not claims.user_id:
        raise AuthError("auth claims missing tenant_id or user_id")

    # Bind the tenant to this transaction. set_config(..., is_local=true)
    # lasts only for the current transaction, which is exactly the lifetime
    # of this request's session — so it cannot leak across requests via
    # connection reuse.
    await session.execute(
        text("SELECT set_config('app.current_tenant', :tid, true)"),
        {"tid": claims.tenant_id},
    )

    return RequestContext(claims=claims, session=session)


CurrentContext = Annotated[RequestContext, Depends(request_context)]
