"""Document upload + inbox listing endpoints."""

from __future__ import annotations

import hashlib
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from sqlalchemy import text

from app.core.config import get_settings
from app.core.errors import NotFoundError, ValidationError
from app.middleware.tenant_context import CurrentContext
from app.models.inbox import (
    InboxItem,
    InboxList,
    OcrTextResponse,
    UploadResponse,
)
from app.services import audit
from app.services.storage import get_storage
from app.workflows import get_dispatcher

router = APIRouter()

ALLOWED_MIME_TYPES: frozenset[str] = frozenset(
    {"application/pdf", "image/jpeg", "image/jpg", "image/png"}
)


@router.post(
    "/documents/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    ctx: CurrentContext,
    file: Annotated[UploadFile, File(...)],
    ingest_channel: str = "web_upload",
) -> UploadResponse:
    if ingest_channel not in {"web_upload", "mobile_capture"}:
        raise ValidationError(
            f"ingest_channel for uploads must be web_upload or mobile_capture, got {ingest_channel!r}"
        )

    mime = (file.content_type or "").lower()
    if mime not in ALLOWED_MIME_TYPES:
        raise ValidationError(
            f"unsupported mime type {mime!r}; allowed: {sorted(ALLOWED_MIME_TYPES)}"
        )

    settings = get_settings()
    payload = await file.read()
    if not payload:
        raise ValidationError("uploaded file is empty")
    if len(payload) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"file exceeds max upload size of {settings.max_upload_bytes} bytes",
        )

    file_hash = hashlib.sha256(payload).hexdigest()
    inbox_id = uuid4()
    filename = file.filename or "upload.bin"
    s3_key = f"tenants/{ctx.claims.tenant_id}/inbox/{inbox_id}/{_safe_filename(filename)}"

    await get_storage().put(s3_key, payload, content_type=mime)

    await ctx.session.execute(
        text(
            """
            INSERT INTO documents_inbox (
                inbox_id, tenant_id, uploaded_by_user_id, original_filename,
                file_hash, file_size_bytes, mime_type, s3_key, ingest_channel
            ) VALUES (
                :id, :tid, :uid, :name, :hash, :size, :mime, :key, :chan
            )
            """
        ),
        {
            "id": str(inbox_id),
            "tid": ctx.claims.tenant_id,
            "uid": ctx.claims.user_id,
            "name": filename,
            "hash": file_hash,
            "size": len(payload),
            "mime": mime,
            "key": s3_key,
            "chan": ingest_channel,
        },
    )
    await audit.emit(
        ctx.session,
        tenant_id=ctx.claims.tenant_id,
        user_id=ctx.claims.user_id,
        action_type="document.uploaded",
        entity_type="documents_inbox",
        entity_id=inbox_id,
        after_state={
            "filename": filename,
            "size_bytes": len(payload),
            "mime_type": mime,
            "ingest_channel": ingest_channel,
            "file_hash": file_hash,
        },
    )
    await ctx.session.commit()

    await get_dispatcher().submit_ocr(inbox_id, UUID(ctx.claims.tenant_id))

    return UploadResponse(
        inbox_id=inbox_id,
        ocr_status="pending",
        file_hash=file_hash,
        file_size_bytes=len(payload),
    )


@router.get("/documents/inbox", response_model=InboxList)
async def list_inbox(ctx: CurrentContext, limit: int = 50, offset: int = 0) -> InboxList:
    if limit < 1 or limit > 200:
        raise ValidationError("limit must be between 1 and 200")
    rows = (
        await ctx.session.execute(
            text(
                """
                SELECT inbox_id, original_filename, file_size_bytes, page_count,
                       mime_type, ocr_status, ocr_provider_used, ocr_error,
                       ingest_channel, parse_status, routing_status, uploaded_at
                FROM documents_inbox
                ORDER BY uploaded_at DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            {"limit": limit, "offset": offset},
        )
    ).all()
    total_row = (
        await ctx.session.execute(text("SELECT COUNT(*) FROM documents_inbox"))
    ).scalar_one()
    items = [
        InboxItem(
            inbox_id=r[0],
            original_filename=r[1],
            file_size_bytes=r[2],
            page_count=r[3],
            mime_type=r[4],
            ocr_status=r[5],
            ocr_provider_used=r[6],
            ocr_error=r[7],
            ingest_channel=r[8],
            parse_status=r[9],
            routing_status=r[10],
            uploaded_at=r[11],
        )
        for r in rows
    ]
    return InboxList(items=items, total=int(total_row))


@router.get("/documents/inbox/{inbox_id}/ocr", response_model=OcrTextResponse)
async def get_ocr_text(ctx: CurrentContext, inbox_id: UUID) -> OcrTextResponse:
    row = (
        await ctx.session.execute(
            text(
                """
                SELECT ocr_status, ocr_text, ocr_provider_used, page_count, ocr_error
                FROM documents_inbox
                WHERE inbox_id = :id
                """
            ),
            {"id": str(inbox_id)},
        )
    ).first()
    if row is None:
        raise NotFoundError("document not found")
    return OcrTextResponse(
        inbox_id=inbox_id,
        ocr_status=row[0],
        ocr_text=row[1],
        ocr_provider_used=row[2],
        page_count=row[3],
        ocr_error=row[4],
    )


def _safe_filename(filename: str) -> str:
    # Basic path-safety: strip directory components and keep a small set of
    # filesystem-friendly characters. Storage keys must be predictable.
    name = filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    return "".join(c if c.isalnum() or c in "._-+ " else "_" for c in name) or "upload.bin"
