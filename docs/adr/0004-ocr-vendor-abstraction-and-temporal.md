# ADR-0004 — OCR vendor abstraction + Temporal-backed pipeline

- Status: Accepted
- Date: 2026-05-09
- Authors: Anuthi Bhansali

## Context

Sprint 2 introduces the first external-call surface in the system: extracting
text from a notice PDF or image. ADR-0003 already says no module hard-codes a
vendor; this ADR records how we apply that principle to OCR specifically and
how the OCR pipeline runs.

Two pressures pull in opposite directions:

1. We want to ship two OCR vendors (Google Document AI as primary, Azure
   Document Intelligence as fallback) so a single-vendor outage doesn't take
   the inbox offline.
2. We want contributors to be able to run the inbox end-to-end without
   credentials for either vendor and without standing up a Temporal cluster.

## Decision

**OCR**: a single `OCRProvider` abstract class with three implementations:

- `GoogleDocumentAIProvider` (primary in production)
- `AzureDocumentIntelligenceProvider` (fallback in production)
- `StubOCRProvider` (CI, local dev, and unit tests; deterministic output)

The factory selects them by name from `OCR_PROVIDER_PRIMARY` /
`OCR_PROVIDER_FALLBACK`. Switching primary from `google_doc_ai` to
`azure_doc_intel` is a config change, not a code change — that's the entire
point.

**Pipeline**: a single async function `run_ocr_pipeline(job)` does the work.
Two dispatchers feed it:

- `InlineDispatcher` runs it in-process as an asyncio task. Used in dev, CI,
  and small single-instance deployments.
- `TemporalDispatcher` submits it to a Temporal cluster as a workflow.
  Production uses this so retry, replay, and visibility are managed by
  Temporal.

Both share the same activity logic, so behavior is identical regardless of
which dispatcher is wired up.

Retry policy:

- 3 attempts against the primary, exponential backoff (1s, 2s, 4s).
- One attempt against the fallback if the primary doesn't recover.
- Persistent failure flips `documents_inbox.ocr_status` to `failed`, records
  the error, fires a Sentry event, and emits an `audit_logs` row with
  `risk_tier=2`.

## Consequences

- No call site imports a vendor SDK. All vendor SDKs are imported lazily
  inside the relevant provider class so a tenant that only uses the fallback
  doesn't have to install the primary's SDK.
- Production deploys must run a Temporal worker. Sprint 2 ships only the
  workflow + activity definitions in `app/workflows/temporal_defs.py`; the
  worker entrypoint lands when production deployment is wired in.
- Tests can flip `WORKFLOW_BACKEND=inline` and exercise the entire pipeline
  with the stub provider. No queue server, no cloud APIs.

## Alternatives considered

- **Direct SDK call from the request handler.** Violates the
  "queue-based for external calls" principle. Rejected.
- **Custom retry queue (Redis + RQ).** Would work, but Sprint 2 sets the
  precedent that all external calls run on Temporal. Mixing queues now means
  re-doing it for the LLM call in Sprint 5.
- **Single OCR vendor.** A single vendor outage takes the inbox offline.
  Rejected on operational grounds.
