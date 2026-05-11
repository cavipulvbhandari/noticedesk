"""Re-run parse-and-route on inbox rows stuck at parse_status='pending'.

The inline workflow dispatcher is fire-and-forget asyncio in the API process,
so an API restart between OCR completion and the parse step leaves rows
permanently stuck. This script invokes ``run_parse_and_route`` for the
given inbox ids using the configured DATABASE_URL and LLM provider.

Usage (from apps/api):

    BYPASS_RLS_DATABASE_URL="postgresql://noticedesk:noticedesk@localhost:5432/noticedesk_dev" \
        python -m scripts.reroute_inbox <inbox_id> [<inbox_id> ...]

``BYPASS_RLS_DATABASE_URL`` is only used to look up each row's tenant_id
(the app role is blocked by RLS until we set the tenant context, which is
what the lookup is *for*). The parse+route work itself runs through the
normal app role + session_for_tenant.
"""

from __future__ import annotations

import argparse
import asyncio
import os
from uuid import UUID

import asyncpg

from app.workflows.document_parsing_and_routing import (
    ParseAndRouteJob,
    run_parse_and_route,
)


async def _lookup_tenant(bypass_url: str, inbox_id: UUID) -> UUID | None:
    conn = await asyncpg.connect(bypass_url)
    try:
        row = await conn.fetchrow(
            "SELECT tenant_id FROM documents_inbox WHERE inbox_id = $1",
            inbox_id,
        )
    finally:
        await conn.close()
    return row["tenant_id"] if row else None


async def main(inbox_ids: list[UUID]) -> None:
    bypass_url = os.environ.get("BYPASS_RLS_DATABASE_URL")
    if not bypass_url:
        raise SystemExit(
            "BYPASS_RLS_DATABASE_URL must be set to a Postgres URL using a role "
            "with BYPASSRLS (e.g. the 'noticedesk' migration role). Example:\n"
            '  postgresql://noticedesk:noticedesk@localhost:5432/noticedesk_dev'
        )
    for inbox_id in inbox_ids:
        tenant_id = await _lookup_tenant(bypass_url, inbox_id)
        if tenant_id is None:
            print(f"× {inbox_id}: not found")
            continue
        print(f"→ {inbox_id} (tenant {tenant_id}): running parse+route ...")
        result = await run_parse_and_route(
            ParseAndRouteJob(inbox_id=inbox_id, tenant_id=tenant_id)
        )
        if result is None:
            print("  result: skipped (already routed, OCR not completed, or parse failed)")
        else:
            print(f"  result: {result!r}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inbox_ids", nargs="+", help="UUIDs of stuck inbox rows")
    args = parser.parse_args()
    asyncio.run(main([UUID(x) for x in args.inbox_ids]))
