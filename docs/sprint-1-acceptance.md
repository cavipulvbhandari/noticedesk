# Sprint 1 — Foundation Scaffold: Acceptance Checklist

The following acceptance criteria are met by the artifacts in this branch.

| # | Criterion | Where it lives | How to verify |
|---|---|---|---|
| 1 | Repository structure follows the layout in the brief. | `apps/`, `packages/`, `infra/`, `docs/` at the repo root. | `tree -L 2 -d` |
| 2 | All 13 database tables created with correct schema, FKs, CHECKs. | `packages/db/migrations/0002_*.sql` through `0008_*.sql`. | `bash packages/db/tests/run_all.sh` |
| 3 | RLS active on every tenant-scoped table. | `packages/db/migrations/0009_row_level_security.sql`. | `tests/07_tenant_isolation.sql` |
| 4 | `audit_logs` is append-only. | `packages/db/migrations/0006_audit_logs.sql`. | `tests/06_audit_log_append_only.sql` |
| 5 | PAN format CHECK rejects invalid PANs. | `clients.pan_format` constraint. | `tests/01_pan_format.sql` |
| 6 | GSTIN format CHECK rejects invalid GSTINs. | `client_registrations.identifier_format`. | `tests/02_gstin_format.sql` |
| 7 | Trigger blocks PAN-mismatched registrations. | `enforce_registration_pan_consistency()`. | `tests/03_registration_pan_consistency.sql` |
| 8 | Two IT registrations for the same client are blocked. | `idx_one_it_reg_per_client` partial unique index. | `tests/04_one_it_registration_per_client.sql` |
| 9 | Matter law must match its registration's type. | `enforce_matter_registration_law()`. | `tests/05_matter_registration_law.sql` |
| 10 | identity.py is unit-tested against valid + invalid inputs. | `apps/api/tests/test_identity.py`. | `pytest` |
| 11 | Auth flow with email/password + Clerk session. | `apps/api/app/core/auth.py` + `apps/web/app/login/page.tsx`. | Manual: visit /login |
| 12 | Backend health endpoint returns 200. | `apps/api/app/routes/health.py`. | `apps/api/tests/test_health.py` |
| 13 | Frontend login + dashboard placeholder show tenant + user name. | `apps/web/app/login/page.tsx`, `apps/web/app/dashboard/page.tsx`. | Manual smoke test |
| 14 | Sentry receives a test error. | `apps/api/app/main.py` initializes Sentry SDK when DSN is set. | Set `SENTRY_DSN`, raise from a route |
| 15 | CI passes lint + type-check. | `.github/workflows/ci.yml`. | Push and watch the `ci` workflow |
| 16 | Two test tenants are isolated. | RLS policies. | `tests/07_tenant_isolation.sql` |
| 17 | `users.clerk_user_id` linking column exists with partial unique index. | `migrations/0010_users_clerk_link.sql`. | `\d users` after migrations |
| 18 | `GET /v1/me` returns the current user + tenant. | `apps/api/app/routes/me.py`. | `curl -H 'X-Dev-User-Id: …' -H 'X-Dev-Tenant-Id: …' /v1/me` |
| 19 | `get_state_name_from_code` resolves GSTIN state codes. | `apps/api/app/services/identity.py`. | `pytest tests/test_identity.py::TestGetStateNameFromCode` |
| 20 | Sidebar + Topbar shell with prototype tokens, Fraunces/DM Sans/JetBrains Mono fonts. | `apps/web/components/shell/`, `tailwind.config.ts`. | `npm run build:web` and visit `/dashboard` |
| 21 | Time-aware "Good morning, {first_name}" greeting in IST. | `apps/web/app/dashboard/page.tsx`. | Visit `/dashboard` between IST hours; verify greeting changes |
| 22 | Phase 1 demo seed loads `Mehta & Associates` + `CA Rohan Mehta`. | `packages/db/seeds/phase1_demo.sql`. | `psql … -f packages/db/seeds/phase1_demo.sql` |

## Out of scope (do not build in Sprint 1)

- Notice parsing
- Drafting
- WhatsApp
- Reminders
- Any agent
- Any feature beyond auth + scaffolding

These are intentionally absent from Sprint 1 per the brief. See the V2-candidate
markers in source for parking-lot items.
