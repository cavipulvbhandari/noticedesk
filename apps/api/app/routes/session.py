"""Session endpoint: returns the logged-in user and their tenant.

This is what the frontend dashboard placeholder calls to render
"Logged in as <name>, tenant <legal_name>".
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

from app.core.errors import NotFoundError
from app.middleware.tenant_context import CurrentContext

router = APIRouter()


@router.get("/session")
async def get_session(ctx: CurrentContext) -> dict[str, Any]:
    user_row = (
        await ctx.session.execute(
            text("SELECT user_id, name, role, email FROM users WHERE user_id = :uid"),
            {"uid": ctx.claims.user_id},
        )
    ).first()
    if user_row is None:
        raise NotFoundError("user not found in tenant")

    tenant_row = (
        await ctx.session.execute(
            text("SELECT tenant_id, legal_name FROM tenants WHERE tenant_id = :tid"),
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
        },
        "tenant": {
            "tenant_id": str(tenant_row[0]),
            "legal_name": tenant_row[1],
        },
    }
