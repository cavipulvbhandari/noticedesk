"""Global search across clients (name, PAN) and notices (issue text, DIN).

Used by the topbar search popover. Phase 1 keeps the implementation simple:
case-insensitive ILIKE against three columns. Postgres' GIN/trigram indexes
arrive in a later sprint once we know the query mix.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Query
from sqlalchemy import text

from app.middleware.tenant_context import CurrentContext

router = APIRouter()

QueryString = Annotated[str, Query(min_length=2, max_length=120)]


@router.get("/search")
async def global_search(ctx: CurrentContext, q: QueryString) -> dict[str, Any]:
    like = f"%{q.lower()}%"
    pan_like = f"%{q.upper()}%"  # PAN/GSTIN are uppercase; match either form.

    client_rows = (
        await ctx.session.execute(
            text(
                """
                SELECT client_id, legal_name, pan, entity_type
                FROM clients
                WHERE deleted_at IS NULL
                  AND (LOWER(legal_name) LIKE :like OR pan LIKE :pan_like)
                ORDER BY legal_name ASC
                LIMIT 8
                """
            ),
            {"like": like, "pan_like": pan_like},
        )
    ).mappings().all()

    notice_rows = (
        await ctx.session.execute(
            text(
                """
                SELECT n.notice_id, n.document_type, n.due_date, n.lifecycle_status,
                       n.din_or_rfn, n.raw_extracted_json,
                       c.legal_name AS client_legal_name
                FROM notices n
                JOIN clients c ON c.client_id = n.client_id
                WHERE c.deleted_at IS NULL
                  AND (
                    LOWER(COALESCE(n.raw_extracted_json->>'issue', '')) LIKE :like
                    OR LOWER(COALESCE(n.din_or_rfn, '')) LIKE :like
                    OR LOWER(COALESCE(n.document_type, '')) LIKE :like
                  )
                ORDER BY n.due_date ASC NULLS LAST
                LIMIT 8
                """
            ),
            {"like": like},
        )
    ).mappings().all()

    return {
        "query": q,
        "clients": [
            {
                "client_id": str(r["client_id"]),
                "legal_name": r["legal_name"],
                "pan": r["pan"],
                "entity_type": r["entity_type"],
            }
            for r in client_rows
        ],
        "notices": [
            {
                "notice_id": str(r["notice_id"]),
                "document_type": r["document_type"],
                "due_date": r["due_date"].isoformat() if r["due_date"] else None,
                "lifecycle_status": r["lifecycle_status"],
                "din_or_rfn": r["din_or_rfn"],
                "issue": (
                    (r["raw_extracted_json"] or {}).get("issue")
                    if isinstance(r["raw_extracted_json"], dict)
                    else None
                ),
                "client_legal_name": r["client_legal_name"],
            }
            for r in notice_rows
        ],
    }
