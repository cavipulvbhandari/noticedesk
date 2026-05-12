"""Registration read + write endpoints.

The write side of POST /v1/clients/{id}/registrations lives in routing.py
because the inbox anomaly-resolution flow drives it. This module owns:

- GET   /v1/registrations/{id}/notices — list of all notices for the reg,
                                          grouped client-side by FY (GST)
                                          or AY (IT). Returns flat rows so
                                          the dashboard can also consume.
- PATCH /v1/registrations/{id}         — partial update (jurisdiction
                                          office, status). Identifier and
                                          client_id stay immutable.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.core.errors import NotFoundError, ValidationError
from app.middleware.tenant_context import CurrentContext
from app.services import audit

router = APIRouter()


@router.get("/registrations/{registration_id}/notices")
async def list_registration_notices(
    ctx: CurrentContext, registration_id: UUID
) -> dict[str, Any]:
    """Return every notice for this registration, plus enough context for
    the year-group drilldown UI (client name, PAN, GSTIN/state).

    The UI groups by financial_year for GST registrations and by
    assessment_year for IT registrations; both groupings happen client-side
    so we don't have two near-identical endpoints.
    """
    reg_row = (
        await ctx.session.execute(
            text(
                """
                SELECT r.registration_id, r.registration_type, r.identifier_value,
                       r.state_code, r.state_name, r.jurisdiction_office,
                       r.registration_status,
                       c.client_id, c.legal_name, c.pan
                FROM client_registrations r
                JOIN clients c ON c.client_id = r.client_id
                WHERE r.registration_id = :rid AND c.deleted_at IS NULL
                """
            ),
            {"rid": str(registration_id)},
        )
    ).mappings().first()
    if reg_row is None:
        raise NotFoundError("registration not found")

    notice_rows = (
        await ctx.session.execute(
            text(
                """
                SELECT notice_id, document_type, due_date, hearing_date,
                       authority, financial_year, assessment_year,
                       lifecycle_status, ingest_channel, din_or_rfn,
                       raw_extracted_json
                FROM notices
                WHERE registration_id = :rid
                ORDER BY due_date DESC NULLS LAST
                """
            ),
            {"rid": str(registration_id)},
        )
    ).mappings().all()

    return {
        "registration": {
            "registration_id": str(reg_row["registration_id"]),
            "registration_type": reg_row["registration_type"],
            "identifier_value": reg_row["identifier_value"],
            "state_code": reg_row["state_code"],
            "state_name": reg_row["state_name"],
            "jurisdiction_office": reg_row["jurisdiction_office"],
            "registration_status": reg_row["registration_status"],
            "sync_method": "manual",
            "last_synced_at": None,
        },
        "client": {
            "client_id": str(reg_row["client_id"]),
            "legal_name": reg_row["legal_name"],
            "pan": reg_row["pan"],
        },
        "notices": [
            {
                "notice_id": str(n["notice_id"]),
                "document_type": n["document_type"],
                "due_date": n["due_date"].isoformat() if n["due_date"] else None,
                "hearing_date": n["hearing_date"].isoformat() if n["hearing_date"] else None,
                "authority": n["authority"],
                "financial_year": n["financial_year"],
                "assessment_year": n["assessment_year"],
                "lifecycle_status": n["lifecycle_status"],
                "ingest_channel": n["ingest_channel"],
                "din_or_rfn": n["din_or_rfn"],
                # The seed packs the raw issue text and assignee into
                # raw_extracted_json so the drilldown can render them
                # without joining audit tables.
                "issue": (
                    (n["raw_extracted_json"] or {}).get("issue")
                    if isinstance(n["raw_extracted_json"], dict)
                    else None
                ),
                "assigned_to": (
                    (n["raw_extracted_json"] or {}).get("assigned_to")
                    if isinstance(n["raw_extracted_json"], dict)
                    else None
                ),
            }
            for n in notice_rows
        ],
        "total": len(notice_rows),
    }


class UpdateRegistrationRequest(BaseModel):
    jurisdiction_office: str | None = None
    state_name: str | None = None
    registration_status: str | None = Field(
        default=None,
        pattern=r"^(active|suspended|cancelled|surrendered)$",
    )


@router.patch("/registrations/{registration_id}")
async def update_registration(
    ctx: CurrentContext, registration_id: UUID, body: UpdateRegistrationRequest
) -> dict[str, Any]:
    fields = body.model_dump(exclude_unset=True)
    if not fields:
        raise ValidationError("no fields to update")

    before = (
        await ctx.session.execute(
            text(
                "SELECT jurisdiction_office, state_name, registration_status "
                "FROM client_registrations WHERE registration_id = :rid"
            ),
            {"rid": str(registration_id)},
        )
    ).mappings().first()
    if before is None:
        raise NotFoundError("registration not found")

    set_clauses = ", ".join(f"{k} = :{k}" for k in fields)
    params: dict[str, Any] = {"rid": str(registration_id), **fields}
    await ctx.session.execute(
        text(
            f"UPDATE client_registrations SET {set_clauses}, updated_at = NOW() "
            "WHERE registration_id = :rid"
        ),
        params,
    )

    await audit.emit(
        ctx.session,
        tenant_id=ctx.claims.tenant_id,
        user_id=ctx.claims.user_id,
        action_type="registration.updated",
        entity_type="client_registrations",
        entity_id=registration_id,
        before_state={k: before[k] for k in fields},
        after_state=fields,
        risk_tier=1,
    )
    await ctx.session.commit()
    return {"registration_id": str(registration_id), "updated_fields": list(fields)}
