# Sprint 3 — Parsing Agent + PAN-Centric Routing + Inbox Routing UI

## Acceptance checklist

| # | Criterion | Where it lives | How to verify |
|---|---|---|---|
| 1 | All 8 notice types correctly classified on eval (>90%) | `KNOWN_DOCUMENT_TYPES` + `prompts/document_parsing_v1.md` | `python -m app.agents.evals.eval_runner --mode=real` |
| 2 | PAN extraction >95% on IT notices | parsing-agent sanitiser drops fabrications | eval `--mode=real` |
| 3 | GSTIN extraction >95% on GST notices | same | eval `--mode=real` |
| 4 | Mismatch detection: 0 false negatives | `_resolve_canonical_pan` Step A + DB trigger | `pytest tests/test_routing_logic.py::TestStepA::test_mismatch_zero_false_negatives` |
| 5 | Routing attaches notices when match exists | `_match_or_create_matter` + `_create_notice` | `pytest tests/test_parse_route_pipeline.py::test_routed_creates_notice` |
| 6 | `new_gst_registration_detected` surfaced | Step C, GST branch | `test_new_gst_registration_detected` |
| 7 | `client_not_found` surfaced | Step B | `test_client_not_found` |
| 8 | `pan_gstin_mismatch` surfaced | Step A | `test_pan_gstin_mismatch_blocks` |
| 9 | Parsing + routing completes ≤30 s | timeouts: 60 s on LLM, async pipeline | observe inbox row in `/inbox` |
| 10 | Audit log records every parse + routing decision | `app.services.audit.emit` calls in parsing + routing | `SELECT action_type FROM audit_logs ORDER BY timestamp DESC;` |
| 11 | Manual override creates notice + logs reason | `POST /v1/inbox/{id}/route_manually` | `pytest` + manual test via UI |
| 12 | `/inbox` UI shows pre-seeded i1, i2, i3 with correct chips | `packages/db/seeds/phase1_demo.sql` + `RoutingChip` | apply seed, open `/inbox` |
| 13 | "+ Add client" on i2 pre-fills PAN `AAQCS3456P` | `AnomalyActions` / `AddClientModal` | click button on i2 |

## What's intentionally out of scope

- Limitation calculation (Phase 2)
- Drafting agent (Sprint 5)
- Citation verification (Sprint 5)
- Two-axis dashboard (Sprint 4)
- Client management UI (Sprint 4)
- Auto-creation of GST registrations (always partner-confirmed)

## How to run end-to-end locally

1. Apply migrations to your dev DB:
   ```bash
   DATABASE_URL='postgres://noticedesk:noticedesk@localhost:5432/noticedesk_dev' \
     bash packages/db/tests/run_all.sh
   psql 'postgres://noticedesk:noticedesk@localhost:5432/noticedesk_dev' \
     -f packages/db/seeds/phase1_demo.sql
   ```

2. Start the API with stubs (no external API keys needed):
   ```bash
   cd apps/api
   OCR_PROVIDER_PRIMARY=stub LLM_PROVIDER_PRIMARY=stub \
     uvicorn app.main:app --reload --port 8000
   ```

3. Start the frontend:
   ```bash
   cd apps/web
   npm run dev
   ```

4. Sign in (tenant_id `11111111-…`, user_id `22222222-…`) and open `/inbox`.
   You should see i1 routed, i2 with **+ Add client**, i3 with
   **+ Add registration**, and any uploads you drop in transition through
   `OCR in progress → Routing → Routed`.

## Running the eval suite

- Plumbing smoke (no LLM, runs in CI):
  ```bash
  cd apps/api && python -m app.agents.evals.eval_runner --mode=regex
  ```

- Real-model eval (needs `ANTHROPIC_API_KEY`):
  ```bash
  LLM_PROVIDER_PRIMARY=anthropic ANTHROPIC_API_KEY=sk-… \
    python -m app.agents.evals.eval_runner --mode=real
  ```
