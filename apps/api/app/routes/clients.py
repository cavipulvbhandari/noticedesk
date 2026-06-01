"""Client read + write endpoints (excluding the inbox-anomaly flows).

The write side of POST /v1/clients and POST /v1/clients/{id}/registrations
lives in routes/routing.py because they're also reachable from the inbox
anomaly-resolution path. This module owns:

- GET    /v1/clients              — list with summary counts (slice 1)
- GET    /v1/clients/{id}         — single client + full registration list
- PATCH  /v1/clients/{id}         — partial update of non-PAN fields
- DELETE /v1/clients/{id}         — soft-delete (partner role only,
                                    audit-logged at risk_tier=2)
"""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.core.errors import NotFoundError, ValidationError
from app.middleware.rbac import require_partner_or_above
from app.middleware.tenant_context import CurrentContext, RequestContext
from app.services import audit

# Module-level singleton — fixes ruff B008 (no Depends() in arg defaults).
PartnerContext = Annotated[RequestContext, Depends(require_partner_or_above())]

router = APIRouter()


_OPEN_LIFECYCLE = ("issued", "in_progress", "due", "due_date_over")


@router.get("/clients")
async def list_clients(ctx: CurrentContext) -> dict[str, Any]:
    """Return every active (non-deleted) client in the tenant with summary counts."""
    rows = (
        await ctx.session.execute(
            text(
                """
                SELECT
                    c.client_id,
                    c.pan,
                    c.legal_name,
                    c.trade_name,
                    c.entity_type,
                    c.industry,
                    COALESCE(gst.gst_count, 0)              AS gst_count,
                    COALESCE(gst.state_codes, '{}'::text[]) AS gst_state_codes,
                    COALESCE(n.active_it_count, 0)          AS active_it_count,
                    COALESCE(n.active_gst_count, 0)         AS active_gst_count,
                    n.earliest_open_due_date                AS earliest_open_due_date
                FROM clients c
                LEFT JOIN (
                    SELECT
                        client_id,
                        COUNT(*)::int                              AS gst_count,
                        ARRAY_AGG(state_code ORDER BY state_code)  AS state_codes
                    FROM client_registrations
                    WHERE registration_type = 'GST'
                      AND registration_status = 'active'
                    GROUP BY client_id
                ) gst ON gst.client_id = c.client_id
                LEFT JOIN (
                    SELECT
                        client_id,
                        COUNT(*) FILTER (WHERE law = 'IT')::int  AS active_it_count,
                        COUNT(*) FILTER (WHERE law = 'GST')::int AS active_gst_count,
                        MIN(due_date) FILTER (WHERE due_date IS NOT NULL)
                            AS earliest_open_due_date
                    FROM notices
                    WHERE lifecycle_status = ANY(:open_states)
                    GROUP BY client_id
                ) n ON n.client_id = c.client_id
                WHERE c.deleted_at IS NULL
                ORDER BY c.legal_name ASC
                """
            ),
            {"open_states": list(_OPEN_LIFECYCLE)},
        )
    ).mappings().all()

    return {
        "clients": [
            {
                "client_id": str(r["client_id"]),
                "pan": r["pan"],
                "legal_name": r["legal_name"],
                "trade_name": r["trade_name"],
                "entity_type": r["entity_type"],
                "industry": r["industry"],
                "gst_count": r["gst_count"],
                "gst_state_codes": list(r["gst_state_codes"] or []),
                "active_it_count": r["active_it_count"],
                "active_gst_count": r["active_gst_count"],
                "earliest_open_due_date": (
                    r["earliest_open_due_date"].isoformat()
                    if r["earliest_open_due_date"] is not None
                    else None
                ),
            }
            for r in rows
        ],
        "total": len(rows),
    }


@router.get("/clients/{client_id}")
async def get_client(ctx: CurrentContext, client_id: UUID) -> dict[str, Any]:
    """Return one client + full registration list with per-registration counts."""
    client_row = (
        await ctx.session.execute(
            text(
                """
                SELECT client_id, pan, legal_name, trade_name, entity_type,
                       cin, date_of_incorporation_or_birth, industry,
                       email, phone,
                       created_at, updated_at
                FROM clients
                WHERE client_id = :cid AND deleted_at IS NULL
                """
            ),
            {"cid": str(client_id)},
        )
    ).mappings().first()
    if client_row is None:
        raise NotFoundError("client not found")

    # One trip for registrations + their per-reg active notice count +
    # earliest deadline. The active-notice subquery is correlated to the
    # registration_id, which the idx_notices_due_date partial index covers.
    reg_rows = (
        await ctx.session.execute(
            text(
                """
                SELECT
                    r.registration_id,
                    r.registration_type,
                    r.identifier_value,
                    r.state_code,
                    r.state_name,
                    r.jurisdiction_office,
                    r.registration_status,
                    COALESCE(n.active_count, 0)  AS active_notice_count,
                    n.earliest_open_due_date     AS earliest_open_due_date
                FROM client_registrations r
                LEFT JOIN (
                    SELECT
                        registration_id,
                        COUNT(*)::int  AS active_count,
                        MIN(due_date) FILTER (WHERE due_date IS NOT NULL)
                            AS earliest_open_due_date
                    FROM notices
                    WHERE lifecycle_status = ANY(:open_states)
                    GROUP BY registration_id
                ) n ON n.registration_id = r.registration_id
                WHERE r.client_id = :cid
                ORDER BY r.registration_type DESC,  -- IT before GST
                         r.state_code ASC NULLS FIRST
                """
            ),
            {"cid": str(client_id), "open_states": list(_OPEN_LIFECYCLE)},
        )
    ).mappings().all()

    return {
        "client_id": str(client_row["client_id"]),
        "pan": client_row["pan"],
        "legal_name": client_row["legal_name"],
        "trade_name": client_row["trade_name"],
        "entity_type": client_row["entity_type"],
        "cin": client_row["cin"],
        "date_of_incorporation_or_birth": (
            client_row["date_of_incorporation_or_birth"].isoformat()
            if client_row["date_of_incorporation_or_birth"] is not None
            else None
        ),
        "industry": client_row["industry"],
        "email": client_row["email"],
        "phone": client_row["phone"],
        "registrations": [
            {
                "registration_id": str(r["registration_id"]),
                "registration_type": r["registration_type"],
                "identifier_value": r["identifier_value"],
                "state_code": r["state_code"],
                "state_name": r["state_name"],
                "jurisdiction_office": r["jurisdiction_office"],
                "registration_status": r["registration_status"],
                "active_notice_count": r["active_notice_count"],
                "earliest_open_due_date": (
                    r["earliest_open_due_date"].isoformat()
                    if r["earliest_open_due_date"] is not None
                    else None
                ),
                # Phase 1: every registration is "manual entry · portal sync
                # coming soon" unless we add a portal connector later.
                "sync_method": "manual",
                "last_synced_at": None,
            }
            for r in reg_rows
        ],
    }


class UpdateClientRequest(BaseModel):
    """Non-PAN fields that a partner can edit. PAN is immutable by design —
    it's the canonical identifier that registrations + notices key off.
    """

    legal_name: str | None = Field(default=None, min_length=1, max_length=255)
    trade_name: str | None = None
    entity_type: str | None = None
    industry: str | None = None
    cin: str | None = None
    # Optional — when present, drives the triage checklist email to the
    # client and (Stage 2) the reminder-recipient pool. Loose validation;
    # the DB CHECK constraint catches obvious malformed addresses.
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=40)


@router.patch("/clients/{client_id}")
async def update_client(
    ctx: CurrentContext, client_id: UUID, body: UpdateClientRequest
) -> dict[str, Any]:
    fields = body.model_dump(exclude_unset=True)
    if not fields:
        raise ValidationError("no fields to update")

    before = (
        await ctx.session.execute(
            text(
                "SELECT legal_name, trade_name, entity_type, industry, cin, email, phone "
                "FROM clients WHERE client_id = :cid AND deleted_at IS NULL"
            ),
            {"cid": str(client_id)},
        )
    ).mappings().first()
    if before is None:
        raise NotFoundError("client not found")

    # Build the SET clause from fields actually present in the body.
    set_clauses = ", ".join(f"{k} = :{k}" for k in fields)
    params: dict[str, Any] = {"cid": str(client_id), **fields}
    await ctx.session.execute(
        text(f"UPDATE clients SET {set_clauses}, updated_at = NOW() WHERE client_id = :cid"),
        params,
    )

    await audit.emit(
        ctx.session,
        tenant_id=ctx.claims.tenant_id,
        user_id=ctx.claims.user_id,
        action_type="client.updated",
        entity_type="clients",
        entity_id=client_id,
        before_state={k: before[k] for k in fields},
        after_state=fields,
        risk_tier=1,
    )
    await ctx.session.commit()
    return {"client_id": str(client_id), "updated_fields": list(fields)}


@router.delete("/clients/{client_id}", status_code=status.HTTP_200_OK)
async def delete_client(
    ctx: PartnerContext,
    client_id: UUID,
) -> dict[str, Any]:
    """Soft-delete a client. Partner role only; audit-logged at risk_tier=2.

    The row stays in the database — notices and audit logs reference it via
    FK and we never want to lose that history. Subsequent reads filter it
    out via ``deleted_at IS NULL``. The partial unique index on
    (tenant_id, pan) WHERE deleted_at IS NULL means a partner can re-add
    a client with the same PAN after a soft-delete if they need to.
    """
    before = (
        await ctx.session.execute(
            text(
                "SELECT pan, legal_name FROM clients "
                "WHERE client_id = :cid AND deleted_at IS NULL"
            ),
            {"cid": str(client_id)},
        )
    ).mappings().first()
    if before is None:
        raise NotFoundError("client not found")

    await ctx.session.execute(
        text(
            "UPDATE clients SET deleted_at = NOW(), updated_at = NOW() "
            "WHERE client_id = :cid"
        ),
        {"cid": str(client_id)},
    )

    await audit.emit(
        ctx.session,
        tenant_id=ctx.claims.tenant_id,
        user_id=ctx.claims.user_id,
        action_type="client.deleted",
        entity_type="clients",
        entity_id=client_id,
        before_state={"pan": before["pan"], "legal_name": before["legal_name"]},
        after_state={"deleted_at": "now()"},
        risk_tier=2,
    )
    await ctx.session.commit()
    return {"client_id": str(client_id), "deleted": True}
