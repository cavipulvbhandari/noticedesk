"""Temporal workflow + activity definitions.

This module is only imported when ``WORKFLOW_BACKEND=temporal``. The actual
business logic lives in :mod:`app.workflows.document_ocr` and
:mod:`app.workflows.document_parsing_and_routing`; this file is just the
Temporal binding.
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from temporalio import activity, workflow
else:  # pragma: no cover — only loaded when temporalio is installed
    from temporalio import activity, workflow  # type: ignore[import-not-found]

from app.workflows.document_ocr import OcrJob, run_ocr_pipeline
from app.workflows.document_parsing_and_routing import (
    ParseAndRouteJob,
    run_parse_and_route,
)


@activity.defn(name="run_ocr_pipeline")
async def run_ocr_pipeline_activity(payload: dict[str, str]) -> None:
    await run_ocr_pipeline(OcrJob.from_dict(payload))


@activity.defn(name="run_parse_and_route")
async def run_parse_and_route_activity(payload: dict[str, str]) -> None:
    await run_parse_and_route(ParseAndRouteJob.from_dict(payload))


@workflow.defn(name="DocumentOcrWorkflow")
class DocumentOcrWorkflow:
    @workflow.run
    async def run(self, payload: dict[str, str]) -> None:
        await workflow.execute_activity(
            run_ocr_pipeline_activity,
            payload,
            start_to_close_timeout=timedelta(minutes=5),
        )
        # Chain into Sprint 3 parse+route under the same workflow so the
        # whole pipeline shows as one Temporal trace.
        await workflow.execute_activity(
            run_parse_and_route_activity,
            payload,
            start_to_close_timeout=timedelta(minutes=5),
        )


@workflow.defn(name="DocumentParseAndRouteWorkflow")
class DocumentParseAndRouteWorkflow:
    @workflow.run
    async def run(self, payload: dict[str, str]) -> None:
        await workflow.execute_activity(
            run_parse_and_route_activity,
            payload,
            start_to_close_timeout=timedelta(minutes=5),
        )
