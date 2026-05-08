# NoticeDesk — Architecture Overview

Sprint 1 produces the deployable skeleton described below. Subsequent sprints
add features within this skeleton; the boundaries here are the long-lived
ones.

## Identity (the single most important diagram in this repo)

```
CLIENT (one row per PAN, scoped by tenant)
  ├── IT REGISTRATION  (exactly one — identifier_value = client.pan)
  │     └── matters → notices → drafts → citations
  └── GST REGISTRATIONS (zero-to-many — identifier_value is a 15-char GSTIN
        whose positions 3-12 = client.pan)
        ├── matters → notices → drafts → citations
        └── ... (one row per state GSTIN)
```

Hard invariants:

- Every `notice`, `matter`, `draft`, and intelligence row resolves to a
  `(client_id, registration_id)` pair. Never to a bare PAN/GSTIN string.
- IT registration: `identifier_value = client.pan`.
- GST registration: `SUBSTRING(identifier_value, 3, 10) = client.pan`.
- Reconciliation is enforced by trigger, not by application convention.
  See `0003_clients_registrations.sql`.

## Layers

```
                ┌──────────────────────────┐
   user ──────► │  Next.js (Vercel)        │
                │  apps/web                │
                └──────────────┬───────────┘
                               │  REST/JSON over HTTPS
                ┌──────────────▼───────────┐
                │  FastAPI (AWS Mumbai)    │
                │  apps/api                │
                │   ├─ /v1/health          │
                │   ├─ /v1/session         │
                │   └─ middleware:         │
                │      ├─ AuthVerifier     │
                │      └─ TenantContext    │
                └──────┬─────────────┬─────┘
                       │             │
            ┌──────────▼─┐      ┌────▼──────────┐
            │ PostgreSQL │      │ Temporal +    │   ◄── from Sprint 2 onward
            │ RDS Mumbai │      │ external APIs │
            │   + RLS    │      │ (LLM, OCR…)   │
            └────────────┘      └───────────────┘
```

## Multi-tenancy

Postgres RLS with `app.current_tenant` set per request. Without it, all
queries return zero rows. See ADR-0002.

## Deferred for V2+

Counsel marketplace, boardroom risk engine, Section 65B/BSA 63(4), Account
Aggregator, industry/state playbooks, outcome database, voice-to-strategy,
white-label, ICAI CPE, international tax, direct portal scraping, officer
profiling, outcome prediction. See the Sprint 1 brief for the canonical
exclusion list.
