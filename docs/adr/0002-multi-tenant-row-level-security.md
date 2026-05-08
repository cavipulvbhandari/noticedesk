# ADR-0002 — Multi-tenancy via Postgres row-level security

- Status: Accepted
- Date: 2026-05-08
- Authors: Anuthi Bhansali

## Context

NoticeDesk is multi-tenant from day one: each CA firm is a tenant, and a
firm's data must never be visible to another firm. We needed a primary
defense against cross-tenant leaks that does not rely on every developer
remembering to add `WHERE tenant_id = $1` to every query.

## Decision

Every tenant-scoped table has a `tenant_id` column and a row-level
security (RLS) policy `tenant_isolation` that tests
`tenant_id = current_tenant_id()`. The policy applies to both `USING`
(reads) and `WITH CHECK` (writes), so a session bound to tenant A cannot
even insert rows for tenant B.

The `current_tenant_id()` SQL function reads `app.current_tenant`,
returning NULL when unset (in which case the policy fails closed and zero
rows are visible). The API binds this on every request with
`SET LOCAL app.current_tenant = '<uuid>'`, and tests `0009_row_level_security.sql`
also uses `FORCE ROW LEVEL SECURITY` so superuser connections do not bypass
the policy.

The `tenants` table itself is intentionally not RLS-restricted — the API
layer chooses which tenant a session belongs to and must be able to look up
its metadata before binding.

## Consequences

- Forgetting to scope by tenant_id in application code degrades to "see no
  rows" rather than "see another firm's rows". This is the exact failure
  mode we want.
- Tests run as a non-bypassing role (`noticedesk_app`) so RLS is exercised
  the same way as production.
- Audit logs are RLS-restricted too; they remain append-only via separate
  triggers blocking UPDATE/DELETE/TRUNCATE.

## Alternatives considered

- **Schema-per-tenant.** Strong isolation, but operationally heavy at the
  scale we expect (hundreds of firms).
- **Row scoping in application code only.** Too easy to forget; rejected.
