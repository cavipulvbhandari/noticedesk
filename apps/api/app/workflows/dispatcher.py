"""Workflow dispatcher: Temporal in production, inline in dev/test.

Both backends ultimately call :func:`run_ocr_pipeline` (and the Sprint 3
parse-and-route pipeline), so the workflow behavior is identical regardless
of where it runs. The dispatcher choice is a config flag
(``WORKFLOW_BACKEND``), not a code change.
"""

from __future__ import annotations

import abc
import asyncio
from functools import lru_cache
from uuid import UUID

from app.core.config import get_settings
from app.core.logging import get_logger
from app.workflows.document_ocr import OcrJob, run_ocr_pipeline
from app.workflows.document_parsing_and_routing import (
    ParseAndRouteJob,
    run_parse_and_route,
)

logger = get_logger(__name__)


class WorkflowDispatcher(abc.ABC):
    @abc.abstractmethod
    async def submit_ocr(self, inbox_id: UUID, tenant_id: UUID) -> str:
        """Schedule an OCR run. Returns a workflow id (or local task id)."""

    @abc.abstractmethod
    async def submit_parse_and_route(self, inbox_id: UUID, tenant_id: UUID) -> str:
        """Schedule the Sprint 3 parse-and-route pipeline."""

    async def drain(self) -> None:
        """Await any in-flight tasks. Used by tests to flush the inline dispatcher.

        The Temporal dispatcher runs against an external cluster, so this is a
        no-op for it.
        """


class InlineDispatcher(WorkflowDispatcher):
    """Runs the workflow as a fire-and-forget asyncio task in the same process.

    Acceptable for dev, CI, and small single-instance deployments. Production
    should use :class:`TemporalDispatcher` so retries, replay, and visibility
    are managed by Temporal — see ADR-0003.
    """

    def __init__(self) -> None:
        # Per-loop task set so a test that creates a fresh event loop never
        # inherits dangling tasks from a previous one (pytest-asyncio creates
        # a new loop per test by default).
        self._inflight: dict[int, set[asyncio.Task[None]]] = {}

    def _bag_for_loop(self) -> set[asyncio.Task[None]]:
        loop = asyncio.get_running_loop()
        return self._inflight.setdefault(id(loop), set())

    async def submit_ocr(self, inbox_id: UUID, tenant_id: UUID) -> str:
        job = OcrJob(inbox_id=inbox_id, tenant_id=tenant_id)
        bag = self._bag_for_loop()
        task = asyncio.create_task(self._run_ocr_then_parse(job))
        bag.add(task)
        task.add_done_callback(bag.discard)
        return f"inline:{inbox_id}"

    async def submit_parse_and_route(self, inbox_id: UUID, tenant_id: UUID) -> str:
        job = ParseAndRouteJob(inbox_id=inbox_id, tenant_id=tenant_id)
        bag = self._bag_for_loop()
        task = asyncio.create_task(self._run_parse_and_route(job))
        bag.add(task)
        task.add_done_callback(bag.discard)
        return f"inline:parse:{inbox_id}"

    async def _run_ocr_then_parse(self, job: OcrJob) -> None:
        try:
            await run_ocr_pipeline(job)
        except Exception:  # noqa: BLE001
            logger.exception("inline_workflow_crashed", inbox_id=str(job.inbox_id))
            return
        # Chain into Sprint 3: parse + route. The pipeline itself checks
        # ocr_status='completed' before doing anything.
        try:
            await run_parse_and_route(
                ParseAndRouteJob(inbox_id=job.inbox_id, tenant_id=job.tenant_id)
            )
        except Exception:  # noqa: BLE001
            logger.exception("inline_parse_route_crashed", inbox_id=str(job.inbox_id))

    async def _run_parse_and_route(self, job: ParseAndRouteJob) -> None:
        try:
            await run_parse_and_route(job)
        except Exception:  # noqa: BLE001
            logger.exception("inline_parse_route_crashed", inbox_id=str(job.inbox_id))

    async def drain(self) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        bag = self._inflight.get(id(loop))
        if not bag:
            return
        # Snapshot — _run's done-callback discards from the same set.
        await asyncio.gather(*list(bag), return_exceptions=True)


class TemporalDispatcher(WorkflowDispatcher):
    """Submits the workflow to a Temporal cluster.

    The actual workflow class lives at module load time; importing it lazily
    keeps the temporalio dependency optional for dev installs.
    """

    def __init__(self) -> None:
        self._client = None

    async def _ensure_client(self):
        if self._client is not None:
            return self._client
        try:
            from temporalio.client import Client  # type: ignore[import-not-found]
        except ImportError as e:
            raise RuntimeError(
                "temporalio is not installed; either install it or set "
                "WORKFLOW_BACKEND=inline"
            ) from e
        s = get_settings()
        self._client = await Client.connect(s.temporal_host, namespace=s.temporal_namespace)
        return self._client

    async def submit_ocr(self, inbox_id: UUID, tenant_id: UUID) -> str:
        client = await self._ensure_client()
        s = get_settings()
        from app.workflows.temporal_defs import DocumentOcrWorkflow  # local import

        handle = await client.start_workflow(
            DocumentOcrWorkflow.run,
            OcrJob(inbox_id=inbox_id, tenant_id=tenant_id).to_dict(),
            id=f"document-ocr-{inbox_id}",
            task_queue=s.temporal_task_queue,
        )
        return handle.id

    async def submit_parse_and_route(self, inbox_id: UUID, tenant_id: UUID) -> str:
        client = await self._ensure_client()
        s = get_settings()
        from app.workflows.temporal_defs import DocumentParseAndRouteWorkflow

        handle = await client.start_workflow(
            DocumentParseAndRouteWorkflow.run,
            ParseAndRouteJob(inbox_id=inbox_id, tenant_id=tenant_id).to_dict(),
            id=f"document-parse-route-{inbox_id}",
            task_queue=s.temporal_task_queue,
        )
        return handle.id


@lru_cache(maxsize=1)
def get_dispatcher() -> WorkflowDispatcher:
    backend = get_settings().workflow_backend
    if backend == "inline":
        return InlineDispatcher()
    if backend == "temporal":
        return TemporalDispatcher()
    raise RuntimeError(f"unknown WORKFLOW_BACKEND: {backend!r}")
