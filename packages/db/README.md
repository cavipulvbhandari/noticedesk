# @noticedesk/db

PostgreSQL 16+ schema and migrations for NoticeDesk.

## Migrations

Migrations are forward-only, numbered, idempotent within their own scope, and
applied in lexicographic order:

- `0001_extensions.sql` — required Postgres extensions
- `0002_tenants_users.sql` — tenant + user tables
- `0003_clients_registrations.sql` — PAN-centric client + registration tables and triggers
- `0004_matters_notices.sql` — matters and notices, with PAN/GSTIN reconciliation columns
- `0005_documents_drafts_citations.sql` — documents, drafts, citations
- `0006_audit_logs.sql` — append-only audit log with UPDATE/DELETE block trigger
- `0007_cross_adjudication_flags.sql` — cross-adjudication flags between IT and GST
- `0008_reminders_billing.sql` — reminders and billing entries
- `0009_row_level_security.sql` — RLS policies on every tenant-scoped table

## Applying migrations

Local dev (assumes `DATABASE_URL` env var pointing at a Postgres 16 instance):

```bash
make migrate
```

Or directly:

```bash
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f migrations/0001_extensions.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f migrations/0002_tenants_users.sql
# ...etc
```

## Tenant context for RLS

Every connection that reads tenant data must set `app.current_tenant`:

```sql
SET app.current_tenant = '00000000-0000-0000-0000-000000000001';
```

The API does this in middleware on every request. Without it, RLS policies
filter all rows out (i.e. queries return empty).

## Tests

`tests/` contains pgTAP-style assertions runnable via `psql`:

- `tests/01_pan_format.sql`
- `tests/02_gstin_format.sql`
- `tests/03_registration_pan_consistency.sql`
- `tests/04_one_it_registration_per_client.sql`
- `tests/05_matter_registration_law.sql`
- `tests/06_audit_log_append_only.sql`
- `tests/07_tenant_isolation.sql`
