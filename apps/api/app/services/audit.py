"""Audit-log writer.

Every state-changing action emits an immutable event into ``audit_logs``.
The table itself is RLS-restricted by tenant_id and is append-only at the
trigger level; this helper just keeps the call sites uniform.
"""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def emit(
    session: AsyncSession,
    *,
    tenant_id: UUID | str,
    action_type: str,
    entity_type: str,
    entity_id: UUID | str | None,
    user_id: UUID | str | None = None,
    before_state: dict[str, Any] | None = None,
    after_state: dict[str, Any] | None = None,
    risk_tier: int | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    """Append one audit-log row. Caller must have already bound app.current_tenant."""
    await session.execute(
        text(
            """
            INSERT INTO audit_logs (
                tenant_id, user_id, action_type, entity_type, entity_id,
                before_state, after_state, ip_address, user_agent, risk_tier
            ) VALUES (
                :tenant_id, :user_id, :action_type, :entity_type, :entity_id,
                CAST(:before_state AS JSONB), CAST(:after_state AS JSONB),
                CAST(:ip_address AS INET), :user_agent, :risk_tier
            )
            """
        ),
        {
            "tenant_id": str(tenant_id),
            "user_id": str(user_id) if user_id else None,
            "action_type": action_type,
            "entity_type": entity_type,
            "entity_id": str(entity_id) if entity_id else None,
            "before_state": json.dumps(before_state) if before_state else None,
            "after_state": json.dumps(after_state) if after_state else None,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "risk_tier": risk_tier,
        },
    )
