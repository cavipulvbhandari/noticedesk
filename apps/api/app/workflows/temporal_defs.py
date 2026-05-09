"""Temporal workflow + activity definitions.

This module is only imported when ``WORKFLOW_BACKEND=temporal``. The actual
business logic lives in :mod:`app.workflows.document_ocr`; this file is just
the Temporal binding so we can stop and rewrite it when the API stabilizes
without touching the pipeline itself.
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from temporalio import activity, workflow
else:  # pragma: no cover — only loaded when temporalio is installed
    from temporalio import activity, workflow  # type: ignore[import-not-found]

from app.workflows.document_ocr import OcrJob, run_ocr_pipeline


@activity.defn(name="run_ocr_pipeline")
async def run_ocr_pipeline_activity(payload: dict[str, str]) -> None:
    await run_ocr_pipeline(OcrJob.from_dict(payload))


@workflow.defn(name="DocumentOcrWorkflow")
class DocumentOcrWorkflow:
    @workflow.run
    async def run(self, payload: dict[str, str]) -> None:
        await workflow.execute_activity(
            run_ocr_pipeline_activity,
            payload,
            start_to_close_timeout=timedelta(minutes=5),
        )
