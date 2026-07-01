# Seam reconciliation — prototype `nd-api.js` → live `/v1` API

The design handoff (`Noticedesk_Landing_Page_Draft`, `server-starter/`) ships a
prototype integration seam, `nd-api.js`, and a minimal **Node + Express**
`server-starter` written to satisfy it. That starter assumes a greenfield —
its `CLAUDE.md` says the real backend is "designed, not yet built."

This repository is **past** that assumption: it already has a production-grade
backend for the same product in a different stack —

- `apps/api` — FastAPI (Python), the system of record for notices/matters,
  drafting, OCR + parsing, audit, auth via tenant-context + Postgres RLS;
- `packages/db` — 17 migrations with RLS + tenant-isolation tests;
- `apps/web` — a Next.js app whose `/app/api/*` proxy routes are the **real**
  seam in this repo, superseding the `.dc.html` prototype and `nd-api.js`.

So "stand up the backend behind the seam" here means **reconcile**, not
rebuild: confirm the existing `/v1` API covers each prototype capability and
fill only the genuine gaps in Python. Adding the Node starter would duplicate a
complete backend in a second language. It was intentionally **not** imported.

## Capability map

| `nd-api.js` function | Prototype endpoint | Live implementation | Web proxy | Status |
|---|---|---|---|---|
| `listNotices()` | `GET /api/notices` | `GET /v1/notices` — filtered, paginated, RLS-scoped (`app/routes/notices.py:70`) | `app/api/notices/route.ts` | ✅ Covered |
| `getNotice(id)` | `GET /api/notices/:id` | `GET /v1/notices/{id}` — notice + client + registration (`app/routes/notices.py:453`) | `app/api/notices/[id]/route.ts` | ✅ Covered |
| `generateDraft(notice)` | `POST /api/notices/:id/draft` | `POST /v1/notices/{id}/draft` — LLM draft + verified citations; draft body via `GET /v1/drafts/{id}` (`app/routes/drafts.py:39`) | `app/api/notices/[id]/draft/route.ts` | ✅ Covered¹ |
| `ingestNotice(file)` | `POST /api/notices/ingest` | `POST /v1/documents/upload` → async OCR → parse → route (`app/routes/documents.py:32`) | `app/api/upload/route.ts` | ✅ Covered² |
| _create from reviewed extraction_ | `POST /api/notices` | `POST /v1/notices` (manual) / `POST /v1/inbox/{id}/route_manually` (`app/routes/notices.py:317`) | `app/api/notices/route.ts` | ✅ Covered |
| _mark as Filed_ | `POST /api/notices/:id/file` | `PATCH /v1/notices/{id}/lifecycle` → `reply_submitted` (`app/routes/notices.py:614`) | `app/api/notices/[id]/lifecycle/route.ts` | ✅ Covered³ |

¹ The prototype calls an LLM directly in the browser and returns `{ body }`.
The live path runs the drafting agent server-side with citation verification;
the reply text is fetched from `GET /v1/drafts/{draft_id}`. RAG over a legal
corpus (pgvector) remains a Phase-2 item on the `server-starter` task list and
is **out of scope** for seam reconciliation — drafting works today.

² Ingestion is an **async workflow** (upload returns an `inbox_id`; the client
polls `GET /v1/inbox/{id}/parsed`), not a single synchronous call. This is by
design — OCR + LLM parse is slow and runs on background workers. The prototype's
synchronous `ingestNotice` is a demo shortcut.

³ There is no dedicated `filed` lifecycle state and none was added: the repo
models notice lifecycle with ten explicit states, and `reply_submitted` (reason
required, audit-logged) is the semantic "reply filed with the authority." A
parallel `filed` state would duplicate that intent and ripple into the UI's
`lib/lifecycle.ts`. The prototype's "Mark as filed" maps to this transition.

## Gap filled in this change

**Per-field confidence on ingestion.** The prototype `ingestNotice` returns
`fields: [{ key, label, value, confidence }]`, and the Review screen renders a
confidence chip per field (≥0.95 emerald, ≥0.90 amber, else orange). The
backend previously emitted only a single document-level `parse_confidence` plus
a bare `fields_needing_review` list — no per-field scores.

The parsing agent now produces a `field_confidences` map:

- prompt bumped to `document_parsing_v2` (v1 retained for replay), which asks
  the model for a per-field 0–1 score;
- the sanitiser (`app/agents/document_parsing.py::_clean_field_confidences`)
  re-validates it — unknown keys dropped, values clamped to `[0, 1]`, any field
  in `fields_needing_review` forced to `0.0`, missing/invalid scores fall back
  to the document-level `parse_confidence`. Every canonical field is always
  present, so the UI can rely on it.

`field_confidences` rides in the existing `raw_parsed_json` / `raw_extracted_json`
JSONB, so it surfaces through `GET /v1/inbox/{id}/parsed` and the notice detail
with **no migration**.

## Explicitly out of scope (later-phase items from `server-starter/CLAUDE.md`)

These are on the starter's task list but are **not** among the four seam
capabilities, and the repo already scopes them to later phases:

- Deadline calendar + reminder worker (schema exists in
  `0008_reminders_billing.sql`; no worker yet).
- RAG / pgvector retrieval for drafting.
- Real Clerk JWT verification (dev-header auth + RLS work today).
- Audit hash-chain (audit log is append-only, trigger-enforced).
