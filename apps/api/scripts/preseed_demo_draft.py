"""Pre-generate a draft on the Acme DRC-01 notice so the partner demo
opens on a populated state instead of burning 60s live on Generate.

Run from apps/api:

    .venv/bin/python -m scripts.preseed_demo_draft

Picks the first ``due_date_over`` GST notice in the tenant — by default
that's n3 (Acme Maharashtra DRC-01) per the demo seed — and runs the same
workflow the UI does (with whichever LLM_PROVIDER_PRIMARY the shell has
configured). Idempotent: if a draft v1 already exists on the matter, it
exits without creating another.
"""

from __future__ import annotations

import asyncio
import sys
from uuid import UUID

from sqlalchemy import text

from app.core.db import session_for_tenant
from app.workflows.drafting import GenerateDraftJob, run_generate_draft

# Demo seed constants — matches packages/db/seeds/phase1_demo.sql.
TENANT_ID = UUID("11111111-1111-1111-1111-111111111111")
USER_ID = UUID("22222222-2222-2222-2222-222222222222")


async def main() -> int:
    async with session_for_tenant(TENANT_ID) as session:
        row = (
            await session.execute(
                text(
                    """
                    SELECT n.notice_id, n.matter_id
                    FROM notices n
                    JOIN clients c ON c.client_id = n.client_id
                    WHERE c.deleted_at IS NULL
                      AND n.lifecycle_status = 'due_date_over'
                      AND n.law = 'GST'
                    ORDER BY n.due_date ASC
                    LIMIT 1
                    """
                )
            )
        ).first()
        if row is None:
            print(
                "no due_date_over GST notice found — did you run `make db-reset`?",
                file=sys.stderr,
            )
            return 1
        notice_id = row[0]
        matter_id = row[1]
        existing = (
            await session.execute(
                text("SELECT 1 FROM drafts WHERE matter_id = :mid LIMIT 1"),
                {"mid": str(matter_id)},
            )
        ).first()
        if existing is not None:
            print(f"draft already exists on matter {matter_id}; skipping.")
            return 0

    job = GenerateDraftJob(
        tenant_id=TENANT_ID,
        user_id=USER_ID,
        matter_id=matter_id,
        notice_id=notice_id,
        tone="formal",
        partner_instructions="",
        include_cross_registration=False,
    )
    print(f"generating demo draft for matter {matter_id} (notice {notice_id})…")
    result = await run_generate_draft(job)
    print(
        f"created draft {result.draft_id} v{result.version} · "
        f"{result.sections_kept} sections · citations {result.citation_summary}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
