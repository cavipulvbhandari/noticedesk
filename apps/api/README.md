# NoticeDesk API

FastAPI backend (Python 3.11+).

## Local development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # fill in values

# Apply migrations to your local Postgres first (see packages/db/README.md).
uvicorn app.main:app --reload --port 8000
```

Health check: `GET http://localhost:8000/v1/health`.

## Auth

Sprint 1 supports Clerk JWT verification (preferred) or, if `AUTH_PROVIDER=dev`,
a development bypass that trusts `X-Dev-User-Id` and `X-Dev-Tenant-Id` headers.
The dev bypass is rejected unless `ENVIRONMENT=development`.

## Tenant context

Every authenticated request goes through `TenantContextMiddleware`, which
resolves the tenant from the auth claims and runs `SET LOCAL app.current_tenant`
on the request's database connection. Without this, RLS hides every row.

## Tests

```bash
pytest
```

Unit tests (identity utility, OCR factory, OCR stub provider, portal
connectors, local storage, email recipient parsing) run without a database.

Integration tests (`test_ocr_pipeline.py`, `test_upload_endpoint.py`,
`test_email_inbound.py`) require `TEST_DATABASE_URL` pointing at a fresh
Postgres with all migrations from `packages/db/migrations/` applied. They are
skipped automatically when the env var isn't set.

## Sprint 2 endpoints

- `POST /v1/documents/upload` — multipart upload (PDF/JPG/PNG ≤ 50 MB),
  computes SHA-256, stores in `Storage`, creates a `documents_inbox` row,
  dispatches the OCR workflow.
- `GET /v1/documents/inbox` — list inbox items for the current tenant.
- `GET /v1/documents/inbox/{id}/ocr` — fetch OCR text for a document.
- `POST /v1/email/inbound` — SES → SNS webhook. Shared-secret authenticated;
  resolves `notices+{slug}@<domain>` to a tenant by `tenants.slug`.

## Workflow backends

`WORKFLOW_BACKEND=inline` runs the OCR pipeline in-process (default for dev
and CI). `WORKFLOW_BACKEND=temporal` submits it to a Temporal cluster — see
`app/workflows/temporal_defs.py` for the workflow + activity definitions.

## OCR providers

Selected by name from `OCR_PROVIDER_PRIMARY` and `OCR_PROVIDER_FALLBACK`.
Known names: `google_doc_ai`, `azure_doc_intel`, `stub`. Switching primary is
a config change, not a code change.
