"""Role-based access control helpers.

Roles match the user_role enum on the users table:
``partner``, ``managing_partner``, ``manager``, ``staff``, ``client``.
"""

from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import text

from app.core.errors import ForbiddenError, NotFoundError
from app.middleware.tenant_context import CurrentContext, RequestContext

Role = str


async def _load_role(ctx: RequestContext) -> Role:
    row = (
        await ctx.session.execute(
            text("SELECT role FROM users WHERE user_id = :uid"),
            {"uid": ctx.claims.user_id},
        )
    ).first()
    if row is None:
        raise NotFoundError("user not found in tenant")
    return row[0]


def require_role(*allowed: Role):
    """Return a FastAPI dependency that 403s unless the user is in ``allowed``."""

    allowed_set = frozenset(allowed)

    async def _dep(ctx: CurrentContext) -> RequestContext:
        role = await _load_role(ctx)
        if role not in allowed_set:
            raise ForbiddenError(
                f"role '{role}' is not permitted",
                details={"required_roles": sorted(allowed_set)},
            )
        return ctx

    return _dep


def require_partner_or_above():
    return require_role("partner", "managing_partner")


def require_staff_or_above():
    return require_role("partner", "managing_partner", "manager", "staff")


__all__: Iterable[str] = (
    "require_role",
    "require_partner_or_above",
    "require_staff_or_above",
)
