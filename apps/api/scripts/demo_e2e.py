"""End-to-end demo script: upload → OCR → parse → route → draft.

Run from apps/api:

    .venv/bin/python -m scripts.demo_e2e [path/to/notice.pdf]

If no path is provided, a tiny in-memory PDF is uploaded so the demo runs
even on a machine with no sample file.

What it does:
  1. POST /v1/documents/upload with the file
  2. Poll the inbox row every 0.5s until routing_status leaves 'pending'
     or 30s elapse
  3. If a notice was created, generate a draft on that notice (calls the
     drafting workflow inline)
  4. Print every step's outcome so the demo runner can read along

Designed to work with STUB_DEFAULT_CANNED=acme_mh_asmt10 so any PDF
filename routes to Acme Maharashtra during the demo. Without that env
var, only "GST Notice.pdf" / "drc-01.pdf" filenames produce canned
parser output.
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)

import asyncio  # noqa: E402
import os  # noqa: E402
import pathlib  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from uuid import UUID  # noqa: E402

import httpx  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.db import session_for_tenant  # noqa: E402
from app.workflows.drafting import GenerateDraftJob, run_generate_draft  # noqa: E402

TENANT_ID = UUID("11111111-1111-1111-1111-111111111111")
USER_ID = UUID("22222222-2222-2222-2222-222222222222")
API_BASE = os.environ.get("DEMO_API_BASE", "http://localhost:8000")

# A 1-page valid PDF — used when the caller doesn't supply one. Built by
# hand because adding reportlab as a dependency for one demo file is overkill.
_TINY_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]"
    b"/Contents 4 0 R/Resources<<>>>>endobj\n"
    b"4 0 obj<</Length 44>>stream\n"
    b"BT /F1 12 Tf 72 720 Td (NoticeDesk demo upload) Tj ET\n"
    b"endstream endobj\n"
    b"xref\n0 5\n"
    b"0000000000 65535 f \n"
    b"0000000010 00000 n \n"
    b"0000000053 00000 n \n"
    b"0000000098 00000 n \n"
    b"0000000168 00000 n \n"
    b"trailer<</Size 5/Root 1 0 R>>\n"
    b"startxref\n243\n%%EOF\n"
)


def _headers() -> dict[str, str]:
    return {
        "X-Dev-User-Id": str(USER_ID),
        "X-Dev-Tenant-Id": str(TENANT_ID),
    }


async def _upload(filename: str, payload: bytes) -> str:
    url = f"{API_BASE}/v1/documents/upload?ingest_channel=web_upload"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            url,
            headers=_headers(),
            files={"file": (filename, payload, "application/pdf")},
        )
    if resp.status_code != 201:
        raise SystemExit(f"upload failed ({resp.status_code}): {resp.text[:300]}")
    body = resp.json()
    inbox_id = body["inbox_id"]
    print(f"[1/4] uploaded → inbox_id={inbox_id}")
    return inbox_id


async def _wait_for_route(inbox_id: str, timeout_s: float = 30.0) -> dict:
    """Poll the inbox row until OCR + parse + route finish."""
    deadline = time.monotonic() + timeout_s
    async with session_for_tenant(TENANT_ID) as session:
        while time.monotonic() < deadline:
            row = (
                await session.execute(
                    text(
                        """
                        SELECT inbox_id, ocr_status, parse_status, routing_status,
                               parsed_to_notice_id, original_filename
                        FROM documents_inbox
                        WHERE inbox_id = :iid
                        """
                    ),
                    {"iid": inbox_id},
                )
            ).mappings().first()
            if row is None:
                raise SystemExit("inbox row vanished mid-poll")
            print(
                f"   poll: ocr={row['ocr_status']:10s} "
                f"parse={row['parse_status'] or '-':10s} "
                f"route={row['routing_status'] or '-':30s}"
            )
            done = (
                row["ocr_status"] == "completed"
                and row["parse_status"] == "completed"
                and row["routing_status"] not in ("pending", None, "in_progress")
            )
            if done:
                return dict(row)
            await asyncio.sleep(0.5)
    raise SystemExit("timed out waiting for route")


async def _fetch_notice(notice_id: UUID) -> dict:
    async with session_for_tenant(TENANT_ID) as session:
        row = (
            await session.execute(
                text(
                    """
                    SELECT n.notice_id, n.matter_id, n.document_type, n.due_date,
                           c.legal_name AS client_legal_name,
                           r.identifier_value AS registration_identifier
                    FROM notices n
                    JOIN clients c ON c.client_id = n.client_id
                    JOIN client_registrations r ON r.registration_id = n.registration_id
                    WHERE n.notice_id = :nid
                    """
                ),
                {"nid": str(notice_id)},
            )
        ).mappings().first()
    return dict(row) if row else {}


async def _generate_draft(notice: dict) -> None:
    job = GenerateDraftJob(
        tenant_id=TENANT_ID,
        user_id=USER_ID,
        matter_id=UUID(str(notice["matter_id"])),
        notice_id=UUID(str(notice["notice_id"])),
        tone="formal",
        partner_instructions="",
        include_cross_registration=False,
    )
    print("[4/4] generating draft …")
    result = await run_generate_draft(job)
    print(
        f"        ok → draft_id={result.draft_id} v{result.version}  "
        f"citations={result.citation_summary}"
    )
    print()
    print("Open the matter view:")
    print(f"  http://localhost:3000/matters/{notice['notice_id']}")
    print("Then click the 'Draft reply' tab.")


async def main() -> int:
    path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if path is not None and not path.exists():
        raise SystemExit(f"no such file: {path}")
    filename = (path.name if path else "GST Notice.pdf")
    payload = path.read_bytes() if path else _TINY_PDF

    fallback = os.environ.get("STUB_DEFAULT_CANNED", "(unset)")
    print("== NoticeDesk e2e demo ==")
    print(f"   API     : {API_BASE}")
    print(f"   file    : {filename} ({len(payload)} bytes)")
    print(f"   tenant  : {TENANT_ID}")
    print(f"   stub fallback: STUB_DEFAULT_CANNED={fallback}")
    print()

    inbox_id = await _upload(filename, payload)
    print("[2/4] polling for OCR + parse + route …")
    row = await _wait_for_route(inbox_id)
    print(f"        routing_status={row['routing_status']}")

    notice_id = row["parsed_to_notice_id"]
    if notice_id is None:
        print()
        print("[3/4] no notice was created — the inbox row landed in an anomaly state.")
        print("       Resolve it manually from /inbox (Add Client / Add Registration / Reject)")
        print("       and re-run this script. Common causes:")
        print("         - filename didn't match any canned parser entry and")
        print("           STUB_DEFAULT_CANNED was not set, so PAN/GSTIN extraction failed")
        print("         - the canned PAN/GSTIN doesn't correspond to a seeded client")
        return 0
    notice = await _fetch_notice(notice_id)
    print(
        f"[3/4] notice created → {notice['document_type']} for {notice['client_legal_name']} "
        f"({notice['registration_identifier']})"
    )

    await _generate_draft(notice)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
