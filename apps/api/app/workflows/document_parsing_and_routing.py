"""Sprint 3 pipeline: parse the OCR text, then route the resulting notice.

Triggered by ``document_ocr_workflow`` once OCR succeeds. Reads the row,
calls the parsing agent, persists the structured JSON, then runs the
routing agent which either creates ``matters`` + ``notices`` rows or flags
the inbox row with an anomaly status the UI surfaces.

Errors during parsing flip ``documents_inbox.parse_status='failed'`` and
emit an audit row; routing errors are non-fatal (the inbox row keeps its
``parse_status='completed'`` but ``routing_status`` records the anomaly).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from uuid import UUID

import sentry_sdk
from sqlalchemy import text

from app.agents.document_parsing import ParseInput, parse_document
from app.agents.notice_routing import NoticeRoutingDecision, route_notice
from app.core.db import session_for_tenant
from app.core.logging import get_logger
from app.services import audit
from app.services.llm import LLMError

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class ParseAndRouteJob:
    inbox_id: UUID
    tenant_id: UUID

    @classmethod
    def from_dict(cls, payload: dict[str, str]) -> "ParseAndRouteJob":
        return cls(
            inbox_id=UUID(payload["inbox_id"]),
            tenant_id=UUID(payload["tenant_id"]),
        )

    def to_dict(self) -> dict[str, str]:
        return {"inbox_id": str(self.inbox_id), "tenant_id": str(self.tenant_id)}


async def run_parse_and_route(job: ParseAndRouteJob) -> NoticeRoutingDecision | None:
    log = logger.bind(inbox_id=str(job.inbox_id), tenant_id=str(job.tenant_id))

    async with session_for_tenant(job.tenant_id) as session:
        row = await _fetch_inbox_row(session, job.inbox_id)
        if row is None:
            log.warn("inbox_row_missing")
            return None
        if row["ocr_status"] != "completed":
            log.warn("ocr_not_completed_skip_parse", ocr_status=row["ocr_status"])
            return None
        # Already routed or in-progress — be idempotent.
        if row["routing_status"] != "pending":
            log.info("already_routed_skip", routing_status=row["routing_status"])
            return None

        await session.execute(
            text(
                "UPDATE documents_inbox SET parse_status = 'in_progress' "
                "WHERE inbox_id = :id"
            ),
            {"id": str(job.inbox_id)},
        )
        await session.commit()

    parse_input = ParseInput(
        inbox_id=str(job.inbox_id),
        filename=row["original_filename"],
        ingest_channel=row["ingest_channel"],
        ocr_text=row["ocr_text"] or "",
        ocr_provider=row["ocr_provider_used"],
        page_count=row["page_count"],
    )

    try:
        parsed = await parse_document(parse_input)
    except LLMError as e:
        log.error("document_parsing_failed", error=str(e))
        async with session_for_tenant(job.tenant_id) as session:
            await session.execute(
                text(
                    "UPDATE documents_inbox SET parse_status = 'failed' "
                    "WHERE inbox_id = :id"
                ),
                {"id": str(job.inbox_id)},
            )
            await audit.emit(
                session,
                tenant_id=job.tenant_id,
                action_type="document.parsing.failed",
                entity_type="documents_inbox",
                entity_id=job.inbox_id,
                after_state={"error": str(e)},
                risk_tier=2,
            )
            await session.commit()
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("tenant_id", str(job.tenant_id))
            scope.set_extra("inbox_id", str(job.inbox_id))
            scope.set_extra("error", str(e))
            sentry_sdk.capture_message("document_parsing_failed", level="error")
        return None

    # Persist parsed JSON + emit a parse-completed audit row, then run routing.
    async with session_for_tenant(job.tenant_id) as session:
        await session.execute(
            text(
                """
                UPDATE documents_inbox
                SET raw_parsed_json = CAST(:parsed AS JSONB),
                    parse_status    = 'completed'
                WHERE inbox_id = :id
                """
            ),
            {"id": str(job.inbox_id), "parsed": json.dumps(parsed.payload)},
        )
        await audit.emit(
            session,
            tenant_id=job.tenant_id,
            action_type="document.parsing.completed",
            entity_type="documents_inbox",
            entity_id=job.inbox_id,
            after_state={
                "document_type": parsed.payload.get("document_type"),
                "law": parsed.payload.get("law"),
                "parse_confidence": parsed.payload.get("parse_confidence"),
                "model": parsed.model,
                "prompt_version": parsed.prompt_version,
                "provider": parsed.provider_name,
                "input_tokens": parsed.input_tokens,
                "output_tokens": parsed.output_tokens,
            },
        )

        decision = await route_notice(
            session,
            tenant_id=job.tenant_id,
            inbox_id=job.inbox_id,
            parsed=parsed.payload,
            ingest_channel=row["ingest_channel"],
        )
        await session.commit()
    return decision


async def _fetch_inbox_row(session, inbox_id: UUID) -> dict | None:
    row = (
        await session.execute(
            text(
                """
                SELECT ocr_status, ocr_text, ocr_provider_used, page_count,
                       original_filename, ingest_channel, routing_status
                FROM documents_inbox
                WHERE inbox_id = :id
                """
            ),
            {"id": str(inbox_id)},
        )
    ).first()
    if row is None:
        return None
    return {
        "ocr_status": row[0],
        "ocr_text": row[1],
        "ocr_provider_used": row[2],
        "page_count": row[3],
        "original_filename": row[4],
        "ingest_channel": row[5],
        "routing_status": row[6],
    }
