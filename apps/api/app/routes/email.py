"""SES inbound email webhook.

Wire-up:

  AWS SES inbound rule (notices+*@noticedesk.in)
    → SNS topic
    → HTTPS endpoint at /v1/email/inbound

The webhook is signed with a shared secret (``EMAIL_INBOUND_WEBHOOK_SECRET``)
sent in the ``X-Webhook-Secret`` header. The recipient address determines
the tenant: ``notices+{slug}@<email_inbound_domain>`` resolves to the tenant
with that slug. Each PDF / JPG / PNG attachment becomes one ``documents_inbox``
row with ``ingest_channel='email'``.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import re
from uuid import UUID, uuid4

from fastapi import APIRouter, Header, HTTPException, status
from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import session_for_tenant
from app.core.errors import AuthError, ValidationError
from app.core.logging import get_logger
from app.models.inbox import EmailInboundPayload, EmailInboundResponse
from app.routes.documents import ALLOWED_MIME_TYPES
from app.services import audit
from app.services.storage import get_storage
from app.workflows import get_dispatcher

logger = get_logger(__name__)
router = APIRouter()

_RECIPIENT_RE = re.compile(r"notices\+([a-z0-9-]+)@(?P<domain>[a-z0-9.-]+)", re.IGNORECASE)


@router.post("/email/inbound", response_model=EmailInboundResponse)
async def email_inbound(
    payload: EmailInboundPayload,
    x_webhook_secret: str | None = Header(default=None, alias="X-Webhook-Secret"),
) -> EmailInboundResponse:
    settings = get_settings()
    if not settings.email_inbound_webhook_secret:
        raise AuthError("email inbound webhook is not configured")
    if not x_webhook_secret or not hmac.compare_digest(
        x_webhook_secret, settings.email_inbound_webhook_secret
    ):
        raise AuthError("invalid webhook secret")

    slug = _extract_slug(payload.recipient, settings.email_inbound_domain)
    if slug is None:
        raise ValidationError(
            f"recipient {payload.recipient!r} does not match notices+<slug>@{settings.email_inbound_domain}"
        )

    tenant_id = await _resolve_tenant_by_slug(slug)
    if tenant_id is None:
        # Don't raise 404 — SES retries permanently on 5xx and we don't want
        # to bounce email for an unknown firm. Return 200 with skipped count.
        logger.warn("email_inbound_unknown_slug", slug=slug, sender=payload.sender)
        return EmailInboundResponse(accepted=0, skipped=len(payload.attachments), inbox_ids=[])

    accepted: list[UUID] = []
    skipped = 0

    for attachment in payload.attachments:
        mime = (attachment.mime_type or "").lower()
        if mime not in ALLOWED_MIME_TYPES:
            skipped += 1
            continue

        try:
            content = base64.b64decode(attachment.content_b64, validate=True)
        except (ValueError, base64.binascii.Error):
            skipped += 1
            continue

        if len(content) == 0 or len(content) > settings.max_upload_bytes:
            skipped += 1
            continue

        inbox_id = uuid4()
        file_hash = hashlib.sha256(content).hexdigest()
        s3_key = f"tenants/{tenant_id}/inbox/{inbox_id}/{_safe_filename(attachment.filename)}"

        await get_storage().put(s3_key, content, content_type=mime)

        async with session_for_tenant(tenant_id) as session:
            await session.execute(
                text(
                    """
                    INSERT INTO documents_inbox (
                        inbox_id, tenant_id, original_filename, file_hash,
                        file_size_bytes, mime_type, s3_key, ingest_channel,
                        ingest_metadata
                    ) VALUES (
                        :id, :tid, :name, :hash, :size, :mime, :key, 'email',
                        CAST(:meta AS JSONB)
                    )
                    """
                ),
                {
                    "id": str(inbox_id),
                    "tid": str(tenant_id),
                    "name": attachment.filename,
                    "hash": file_hash,
                    "size": len(content),
                    "mime": mime,
                    "key": s3_key,
                    "meta": _email_metadata_json(payload),
                },
            )
            await audit.emit(
                session,
                tenant_id=tenant_id,
                action_type="document.email_received",
                entity_type="documents_inbox",
                entity_id=inbox_id,
                after_state={
                    "sender": payload.sender,
                    "subject": payload.subject,
                    "filename": attachment.filename,
                    "size_bytes": len(content),
                    "file_hash": file_hash,
                },
            )
            await session.commit()

        await get_dispatcher().submit_ocr(inbox_id, tenant_id)
        accepted.append(inbox_id)

    return EmailInboundResponse(
        accepted=len(accepted),
        skipped=skipped,
        inbox_ids=accepted,
    )


def _extract_slug(recipient: str, expected_domain: str) -> str | None:
    if not recipient:
        return None
    m = _RECIPIENT_RE.match(recipient.strip())
    if not m:
        return None
    if m.group("domain").lower() != expected_domain.lower():
        return None
    return m.group(1).lower()


async def _resolve_tenant_by_slug(slug: str) -> UUID | None:
    # tenants is not RLS-restricted, so we can look up without a tenant context.
    from app.core.db import session_local

    async with session_local()() as session:
        row = (
            await session.execute(
                text("SELECT tenant_id FROM tenants WHERE slug = :slug"),
                {"slug": slug},
            )
        ).first()
        if row is None:
            return None
        return UUID(str(row[0]))


def _email_metadata_json(payload: EmailInboundPayload) -> str:
    import json

    return json.dumps(
        {
            "sender_email": payload.sender,
            "recipient": payload.recipient,
            "subject": payload.subject,
            "received_at": payload.received_at.isoformat() if payload.received_at else None,
        }
    )


def _safe_filename(filename: str) -> str:
    name = filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    return "".join(c if c.isalnum() or c in "._-+ " else "_" for c in name) or "attachment.bin"
