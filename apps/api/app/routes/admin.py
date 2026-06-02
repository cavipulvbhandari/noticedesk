"""Internal admin endpoints — not tenant-scoped, protected by X-Admin-Secret.

These routes bypass the normal Clerk/dev auth and RLS by iterating over
every tenant with session_for_tenant(). They are intended for operator use
only (training-data export, model evaluation) and must never be exposed
to partner users.

Authentication: the caller must supply the ``X-Admin-Secret`` header
matching the ``ADMIN_SECRET`` env var. If ADMIN_SECRET is blank or unset,
all requests return 403 to prevent accidental exposure.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Header, HTTPException, Response
from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import session_for_tenant, session_local

router = APIRouter()


def _require_admin(x_admin_secret: str | None) -> None:
    """Raise 403 if the supplied secret doesn't match ADMIN_SECRET."""
    secret = get_settings().admin_secret
    if not secret or x_admin_secret != secret:
        raise HTTPException(status_code=403, detail="forbidden")


@router.get("/admin/training-export")
async def training_export(
    x_admin_secret: str | None = Header(default=None),
) -> Response:
    """Export labeled training pairs as JSONL for LLM fine-tuning.

    Returns one JSON object per line. Each record is a (context, output)
    pair suitable for supervised fine-tuning:

    - ``training_signal``: 'positive' (partner exported) or 'negative'
      (partner regenerated without exporting).
    - ``notice_ocr_text``: up to 60 000 chars of the notice's OCR text.
    - ``matter_context``: client/registration/notice metadata.
    - ``sections``: the partner-approved draft sections (JSONB array).
    - ``edit_count``: how many section edits were made before export.

    Only drafts with training_signal IS NOT NULL are included. Filter on
    ``training_signal`` to build your positive-only training set.

    Usage::

        curl -H 'X-Admin-Secret: <secret>' \\
             https://api.noticedesk.in/v1/admin/training-export \\
             -o training_pairs.jsonl
    """
    _require_admin(x_admin_secret)

    # The tenants table is not RLS-restricted so we can read it without
    # setting a tenant context.
    async with session_local()() as meta_session:
        tenant_rows = (
            await meta_session.execute(
                text("SELECT tenant_id FROM tenants ORDER BY created_at ASC")
            )
        ).fetchall()

    tenant_ids = [r[0] for r in tenant_rows]

    lines: list[str] = []

    for tenant_id in tenant_ids:
        async with session_for_tenant(tenant_id) as session:
            rows = (
                await session.execute(
                    text(
                        """
                        SELECT
                            d.draft_id,
                            d.matter_id,
                            d.version,
                            d.training_signal,
                            d.tone,
                            d.model_used,
                            d.prompt_version,
                            d.sections,
                            d.edits_log,
                            d.generated_at,
                            m.law,
                            m.financial_year,
                            m.assessment_year,
                            c.legal_name           AS client_legal_name,
                            r.registration_type,
                            r.identifier_value,
                            r.state_name,
                            n.notice_id,
                            n.document_type        AS notice_type,
                            n.notice_number,
                            n.authority,
                            n.due_date,
                            LEFT(COALESCE(ib.ocr_text, ''), 60000)
                                                   AS notice_ocr_text
                        FROM drafts d
                        JOIN matters m  ON m.matter_id   = d.matter_id
                        JOIN clients c  ON c.client_id   = m.client_id
                        JOIN client_registrations r
                                        ON r.registration_id = m.registration_id
                        LEFT JOIN notices n
                                        ON n.matter_id   = m.matter_id
                                       AND n.lifecycle_status <> 'closed'
                        LEFT JOIN documents_inbox ib
                                        ON ib.inbox_id   = n.source_inbox_id
                        WHERE d.training_signal IS NOT NULL
                        ORDER BY d.generated_at DESC
                        LIMIT 1
                        """
                    )
                )
            ).mappings().all()

            for row in rows:
                edits_log = row["edits_log"] or []
                edit_count = sum(
                    1 for e in edits_log if e.get("type") == "section_edit"
                )
                record = {
                    "draft_id": str(row["draft_id"]),
                    "matter_id": str(row["matter_id"]),
                    "tenant_id": str(tenant_id),
                    "version": row["version"],
                    "training_signal": row["training_signal"],
                    "tone": row["tone"],
                    "model_used": row["model_used"],
                    "prompt_version": row["prompt_version"],
                    "generated_at": (
                        row["generated_at"].isoformat()
                        if row["generated_at"]
                        else None
                    ),
                    "edit_count": edit_count,
                    "notice_ocr_text": row["notice_ocr_text"] or "",
                    "matter_context": {
                        "client_legal_name": row["client_legal_name"],
                        "registration_type": row["registration_type"],
                        "identifier_value": row["identifier_value"],
                        "state_name": row["state_name"],
                        "law": row["law"],
                        "notice_type": row["notice_type"],
                        "notice_number": row["notice_number"],
                        "authority": row["authority"],
                        "due_date": (
                            row["due_date"].isoformat() if row["due_date"] else None
                        ),
                        "financial_year": row["financial_year"],
                        "assessment_year": row["assessment_year"],
                    },
                    "sections": row["sections"] or [],
                }
                lines.append(json.dumps(record, ensure_ascii=False))

    body = "\n".join(lines) + ("\n" if lines else "")
    return Response(
        content=body,
        media_type="application/x-ndjson",
        headers={
            "Content-Disposition": "attachment; filename=noticedesk_training.jsonl",
            "X-Record-Count": str(len(lines)),
        },
    )
