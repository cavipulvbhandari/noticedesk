"""GET /v1/me — the current user + tenant.

This is the brief-mandated endpoint that the frontend reads on every page
load. It mirrors /v1/session (kept for backwards compatibility) and adds
mfa_enabled, last_login, and clerk_user_id so the UI can render the user
chip and surface a "set up MFA" prompt when relevant.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

from app.core.errors import NotFoundError
from app.middleware.tenant_context import CurrentContext

router = APIRouter()


@router.get("/me")
async def get_me(ctx: CurrentContext) -> dict[str, Any]:
    user_row = (
        await ctx.session.execute(
            text(
                "SELECT user_id, name, role, email, phone, "
                "       mfa_enabled, last_login, clerk_user_id "
                "FROM users WHERE user_id = :uid"
            ),
            {"uid": ctx.claims.user_id},
        )
    ).first()
    if user_row is None:
        raise NotFoundError("user not found in tenant")

    tenant_row = (
        await ctx.session.execute(
            text(
                "SELECT tenant_id, legal_name, pricing_tier "
                "FROM tenants WHERE tenant_id = :tid"
            ),
            {"tid": ctx.claims.tenant_id},
        )
    ).first()
    if tenant_row is None:
        raise NotFoundError("tenant not found")

    return {
        "user": {
            "user_id": str(user_row[0]),
            "name": user_row[1],
            "role": user_row[2],
            "email": user_row[3],
            "phone": user_row[4],
            "mfa_enabled": bool(user_row[5]),
            "last_login": user_row[6].isoformat() if user_row[6] else None,
            "clerk_user_id": user_row[7],
        },
        "tenant": {
            "tenant_id": str(tenant_row[0]),
            "legal_name": tenant_row[1],
            "pricing_tier": tenant_row[2],
        },
    }
