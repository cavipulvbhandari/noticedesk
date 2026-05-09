"""Background workflows.

Architecture principle (ADR-0003 + Sprint 1): all external calls (LLM, OCR,
integration) go through a queue. In production that queue is Temporal; in
dev/test we can also dispatch inline so contributors don't need to run a
Temporal cluster locally. Both backends call the same activity functions, so
the workflow logic is identical regardless of where it runs.
"""

from app.workflows.dispatcher import (
    InlineDispatcher,
    TemporalDispatcher,
    WorkflowDispatcher,
    get_dispatcher,
)

__all__ = [
    "InlineDispatcher",
    "TemporalDispatcher",
    "WorkflowDispatcher",
    "get_dispatcher",
]
