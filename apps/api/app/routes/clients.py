"""Client read endpoints.

The write side (POST /v1/clients, POST /v1/clients/{id}/registrations) lives
in routes/routing.py because the inbox anomaly flow drives those calls. This
module owns the read side used by the /clients UI in the dashboard.

Endpoints:
- GET /v1/clients — list every client in the tenant with the summary counts
  the prototype's clients-list page renders (GST reg count + state codes,
  active IT and GST notice counts, earliest open deadline across both laws).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

from app.middleware.tenant_context import CurrentContext

router = APIRouter()


_OPEN_LIFECYCLE = ("issued", "in_progress", "due", "due_date_over")


@router.get("/clients")
async def list_clients(ctx: CurrentContext) -> dict[str, Any]:
    """Return every client in the tenant with summary counts.

    One round-trip — Postgres does the aggregation. The COALESCE on the
    state_codes array prevents NULL from leaking to the UI when a client has
    no GST registrations yet.
    """
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
                    COALESCE(gst.gst_count, 0)            AS gst_count,
                    COALESCE(gst.state_codes, '{}'::text[]) AS gst_state_codes,
                    COALESCE(n.active_it_count, 0)        AS active_it_count,
                    COALESCE(n.active_gst_count, 0)       AS active_gst_count,
                    n.earliest_open_due_date              AS earliest_open_due_date
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
