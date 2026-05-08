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

Identity-utility tests run without a database. The integration tests under
`tests/integration/` require `TEST_DATABASE_URL` and apply the migrations from
`packages/db/migrations/` before running.
