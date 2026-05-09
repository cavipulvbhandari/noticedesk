# Sprint 2 — Document Upload + OCR + Email Forwarding: Acceptance Checklist

| # | Criterion | Where it lives | How to verify |
|---|---|---|---|
| 1 | User uploads a 5-page PDF and sees it appear in inbox within 3 seconds. | `POST /v1/documents/upload` + `useInboxPoll` (3 s interval). | Run `apps/web` + `apps/api`, sign in, drop a PDF on `/inbox`. |
| 2 | OCR completes for a typical 5-page tax notice within 60 seconds. | `run_ocr_pipeline` with primary 60-s timeout per provider. | Monitor inbox row transition `pending → in_progress → completed`. |
| 3 | If OCR fails, user sees a clear error chip and Sentry receives the alert. | `_mark_failed` writes `ocr_error` and calls `sentry_sdk.capture_message`. | `tests/test_ocr_pipeline.py::test_pipeline_marks_failed_when_no_fallback`. |
| 4 | Document hash stored matches the file actually in S3. | Hash is computed from the same bytes that go to `Storage.put`. | `tests/test_upload_endpoint.py::test_upload_creates_inbox_row_and_runs_ocr`. |
| 5 | Email forward to `notices+mehta-associates@noticedesk.in` creates an inbox row. | `app/routes/email.py` resolves slug → tenant_id, inserts with `ingest_channel='email'`. | `tests/test_email_inbound.py::test_email_creates_inbox_rows`. |
| 6 | Mobile camera capture works on iOS Safari and Android Chrome. | `<input type="file" accept="image/*" capture="environment" />` in `UploadDropzone`. | Manual test on a real device. |
| 7 | All audit events for upload + OCR are logged to audit_logs. | `app/services/audit.py::emit` invoked from upload, email, OCR success, OCR failure. | Read `audit_logs` after the pipeline test. |
| 8 | Switching `OCR_PROVIDER_PRIMARY` works without code changes. | Factory in `app/services/ocr/factory.py`. | `tests/test_ocr_factory.py`. |
| 9 | PortalConnector base class with NoOpConnector + EmailForwardConnector; GSP/AA NOT implemented. | `app/services/portal_connectors/`. | `tests/test_portal_connectors.py`. |
| 10 | `/inbox` page matches prototype's renderInbox visual design. | `apps/web/app/(authed)/inbox/page.tsx` + `components/inbox/*`. | Run `pnpm --filter @noticedesk/web dev`. |
| 11 | `documents_inbox.ingest_channel` enum includes all six values. | `0011_documents_inbox.sql` CHECK constraint. | `tests/09_documents_inbox.sql`. |

## Out of scope (do not build in Sprint 2)

- Notice parsing — Sprint 3.
- Routing logic — Sprint 3.
- Limitation calculation — Phase 2.
- Drafting — Sprint 5.
- Citation verification — Sprint 5.
- WhatsApp ingest — Phase 3.
- GSP / IT-portal AA connectors — Phase 2 (placeholders only).

## Operating notes

- Local dev: `WORKFLOW_BACKEND=inline`, `STORAGE_BACKEND=local`,
  `OCR_PROVIDER_PRIMARY=stub`. No external services required.
- Production: `WORKFLOW_BACKEND=temporal`, `STORAGE_BACKEND=s3`,
  `OCR_PROVIDER_PRIMARY=google_doc_ai`,
  `OCR_PROVIDER_FALLBACK=azure_doc_intel`. Run a Temporal worker against
  the workflow definitions in `app/workflows/temporal_defs.py`.
