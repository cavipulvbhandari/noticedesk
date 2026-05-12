"""Notice list endpoints + dashboard aggregates.

The dashboard surface needs three reads:

- GET /v1/notices?status=&law=&client_id=&registration_id=&from=&to=&page=&page_size=
    Filtered + paginated list, sorted by due_date ASC. Joins clients and
    client_registrations so the row can render the full identity context
    without N+1 follow-ups.
- GET /v1/dashboard/status_counts
    Single row of counts keyed by lifecycle_status. Drives the 8 status
    tabs at the top of the dashboard.
- GET /v1/dashboard/today
    Notices due in the next 7 days inclusive. Brief calls this out
    explicitly even though the prototype doesn't bind it to UI yet.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import text

from app.middleware.tenant_context import CurrentContext

# Annotated query-param aliases — fixes ruff B008 (no Query() in arg defaults).
StatusFilter = Annotated[str | None, Query(pattern="^[a-z_]+$")]
LawFilter = Annotated[Literal["GST", "IT"] | None, Query()]
ClientFilter = Annotated[UUID | None, Query()]
RegistrationFilter = Annotated[UUID | None, Query()]
StateCodeFilter = Annotated[str | None, Query(pattern=r"^[0-9]{2}$")]
FromDateFilter = Annotated[date | None, Query(alias="from")]
ToDateFilter = Annotated[date | None, Query(alias="to")]
PageNumber = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=200)]

router = APIRouter()


_LIFECYCLE_KEYS = (
    "issued",
    "in_progress",
    "due",
    "due_date_over",
    "reply_submitted",
    "acknowledged",
    "order_received",
    "appeal_filed",
    "closed",
    "on_hold",
)


@router.get("/notices")
async def list_notices(
    ctx: CurrentContext,
    status: StatusFilter = None,
    law: LawFilter = None,
    client_id: ClientFilter = None,
    registration_id: RegistrationFilter = None,
    state_code: StateCodeFilter = None,
    from_date: FromDateFilter = None,
    to_date: ToDateFilter = None,
    page: PageNumber = 1,
    page_size: PageSize = 50,
) -> dict[str, Any]:
    """List notices matching the filters, joined with client + registration."""
    where: list[str] = ["c.deleted_at IS NULL"]
    params: dict[str, Any] = {}
    if status is not None:
        where.append("n.lifecycle_status = :status")
        params["status"] = status
    if law is not None:
        where.append("n.law = :law")
        params["law"] = law
    if client_id is not None:
        where.append("n.client_id = :cid")
        params["cid"] = str(client_id)
    if registration_id is not None:
        where.append("n.registration_id = :rid")
        params["rid"] = str(registration_id)
    if state_code is not None:
        where.append("r.state_code = :sc")
        params["sc"] = state_code
    if from_date is not None:
        where.append("n.due_date >= :from_date")
        params["from_date"] = from_date
    if to_date is not None:
        where.append("n.due_date <= :to_date")
        params["to_date"] = to_date

    where_clause = " AND ".join(where) if where else "TRUE"
    params["limit"] = page_size
    params["offset"] = (page - 1) * page_size

    rows = (
        await ctx.session.execute(
            text(
                f"""
                SELECT
                    n.notice_id, n.law, n.document_type, n.due_date,
                    n.financial_year, n.assessment_year, n.lifecycle_status,
                    n.ingest_channel, n.din_or_rfn, n.raw_extracted_json,
                    c.client_id, c.legal_name AS client_legal_name, c.pan AS client_pan,
                    r.registration_id, r.registration_type,
                    r.identifier_value AS registration_identifier,
                    r.state_code  AS registration_state_code,
                    r.state_name  AS registration_state_name
                FROM notices n
                JOIN clients c ON c.client_id = n.client_id
                JOIN client_registrations r ON r.registration_id = n.registration_id
                WHERE {where_clause}
                ORDER BY n.due_date ASC NULLS LAST, n.notice_id ASC
                LIMIT :limit OFFSET :offset
                """
            ),
            params,
        )
    ).mappings().all()

    total_row = (
        await ctx.session.execute(
            text(
                f"""
                SELECT COUNT(*)::int AS total
                FROM notices n
                JOIN clients c ON c.client_id = n.client_id
                JOIN client_registrations r ON r.registration_id = n.registration_id
                WHERE {where_clause}
                """
            ),
            {k: v for k, v in params.items() if k not in ("limit", "offset")},
        )
    ).mappings().first()

    return {
        "notices": [
            {
                "notice_id": str(r["notice_id"]),
                "law": r["law"],
                "document_type": r["document_type"],
                "due_date": r["due_date"].isoformat() if r["due_date"] else None,
                "financial_year": r["financial_year"],
                "assessment_year": r["assessment_year"],
                "lifecycle_status": r["lifecycle_status"],
                "ingest_channel": r["ingest_channel"],
                "din_or_rfn": r["din_or_rfn"],
                "issue": (
                    (r["raw_extracted_json"] or {}).get("issue")
                    if isinstance(r["raw_extracted_json"], dict)
                    else None
                ),
                "assigned_to": (
                    (r["raw_extracted_json"] or {}).get("assigned_to")
                    if isinstance(r["raw_extracted_json"], dict)
                    else None
                ),
                "client_id": str(r["client_id"]),
                "client_legal_name": r["client_legal_name"],
                "client_pan": r["client_pan"],
                "registration_id": str(r["registration_id"]),
                "registration_type": r["registration_type"],
                "registration_identifier": r["registration_identifier"],
                "registration_state_code": r["registration_state_code"],
                "registration_state_name": r["registration_state_name"],
            }
            for r in rows
        ],
        "total": total_row["total"] if total_row else 0,
        "page": page,
        "page_size": page_size,
    }


@router.get("/dashboard/status_counts")
async def dashboard_status_counts(ctx: CurrentContext) -> dict[str, int]:
    """Return counts of notices per lifecycle_status. All 10 keys are
    always present (zero-filled) so the UI doesn't have to defend itself.
    """
    rows = (
        await ctx.session.execute(
            text(
                """
                SELECT n.lifecycle_status, COUNT(*)::int AS count
                FROM notices n
                JOIN clients c ON c.client_id = n.client_id
                WHERE c.deleted_at IS NULL
                GROUP BY n.lifecycle_status
                """
            )
        )
    ).all()
    counts: dict[str, int] = {k: 0 for k in _LIFECYCLE_KEYS}
    for row in rows:
        counts[row[0]] = row[1]
    return counts


@router.get("/dashboard/today")
async def dashboard_today(ctx: CurrentContext) -> dict[str, Any]:
    """Notices due in the next 7 days inclusive of today, plus anything
    already past due that is still open (issued / in_progress / due /
    due_date_over). Used by partners' morning standup view.
    """
    today = date.today()
    horizon = today + timedelta(days=7)
    rows = (
        await ctx.session.execute(
            text(
                """
                SELECT
                    n.notice_id, n.law, n.document_type, n.due_date,
                    n.lifecycle_status, n.raw_extracted_json,
                    c.client_id, c.legal_name AS client_legal_name,
                    r.identifier_value AS reg_identifier
                FROM notices n
                JOIN clients c ON c.client_id = n.client_id
                JOIN client_registrations r ON r.registration_id = n.registration_id
                WHERE c.deleted_at IS NULL
                  AND n.lifecycle_status IN ('issued','in_progress','due','due_date_over')
                  AND n.due_date IS NOT NULL
                  AND n.due_date <= :horizon
                ORDER BY n.due_date ASC
                """
            ),
            {"horizon": horizon},
        )
    ).mappings().all()

    return {
        "today": today.isoformat(),
        "horizon": horizon.isoformat(),
        "notices": [
            {
                "notice_id": str(r["notice_id"]),
                "law": r["law"],
                "document_type": r["document_type"],
                "due_date": r["due_date"].isoformat(),
                "lifecycle_status": r["lifecycle_status"],
                "client_id": str(r["client_id"]),
                "client_legal_name": r["client_legal_name"],
                "registration_identifier": r["reg_identifier"],
                "issue": (
                    (r["raw_extracted_json"] or {}).get("issue")
                    if isinstance(r["raw_extracted_json"], dict)
                    else None
                ),
            }
            for r in rows
        ],
        "total": len(rows),
    }
