# Intern Prerequisites — NoticeDesk & Tender Pocket

What an intern must already know (or learn in a defined ramp window) before
being given a ticket on either project. Everything below is derived from what
the code actually uses today, not from a generic "full-stack" wish list.

Two products, two very different stacks:

| | **NoticeDesk** | **Tender Pocket** |
|---|---|---|
| Domain | Indian direct + indirect tax litigation for CA firms | GeM / government tender bid pipeline |
| Backend | Python 3.11 · FastAPI (plus a Java 21 / Spring Boot port) | Java 21 · Spring Boot 3.4 |
| Frontend | Next.js 14 App Router (in-repo) | Next.js 16 (separate repo, built and served as static assets) |
| Data | PostgreSQL 16, hand-written SQL migrations, Row-Level Security | PostgreSQL via JPA/Hibernate, `ddl-auto=update`, legacy SQLite |
| AI | Claude / OpenAI behind a provider interface | Gemini, called directly |
| Repos | `noticedesk` | `tender-pocket-spring-workflow`, `tender-pocket`, `tender-pocket-java` |

---

## Tier 0 — Non-negotiable for both projects

No intern gets a ticket without these. These are the things where a gap
causes damage, not just slow progress.

### 1. Git and code review discipline
- Branch, commit with a real message, rebase/merge, resolve a conflict, open a
  PR, respond to review comments. No committing straight to `main`.
- Reading a diff critically — most of the work on both codebases is *changing
  existing code*, not writing greenfield files.
- Never commit secrets. Both repos read every credential from the environment
  (`ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `SPRING_MAIL_PASSWORD`,
  `IMAP_PASSWORD`, `DATABASE_URL`). A key in a commit is a rotate-everything
  incident.

### 2. SQL — genuinely, not "I've seen a SELECT"
Both systems are SQL-first. NoticeDesk's backend issues raw SQL through
SQLAlchemy `text()` rather than an ORM, so an intern who only knows ORM
idioms will be lost. Required: joins, `GROUP BY`, aggregates, indexes,
transactions, `NULL` semantics, `ON CONFLICT`, and reading an `EXPLAIN` well
enough to notice a sequential scan on a large table.

### 3. HTTP and REST fundamentals
Methods, status codes, headers, cookies vs. bearer tokens, CORS, multipart
uploads, idempotency. Both apps are plain request/response JSON APIs — no
GraphQL, no gRPC, no websockets.

### 4. The relevant language, at working level
- **NoticeDesk backend:** Python 3.11 — type hints, dataclasses, `async`/`await`,
  virtualenvs, `pip install -e`. The codebase is `mypy --strict` clean, so
  untyped Python will not pass CI.
- **Tender Pocket / NoticeDesk-Java:** Java 21 — records, streams, Optional,
  generics, checked exceptions, Maven lifecycle (`mvn package`, `-DskipTests`).
- **Either frontend:** TypeScript 5 — interfaces vs. types, generics, discriminated
  unions, `strict` mode. `any` is not an acceptable escape hatch.

### 5. Async / concurrency mental model
NoticeDesk's API is async end-to-end (`asyncpg`, `pytest-asyncio`,
`asyncio_mode = auto`); ruff enforces the `ASYNC` lint rules. Tender Pocket runs
background work on `@Scheduled` threads that touch the same tables as live HTTP
requests. Interns must understand blocking calls, why a sync DB driver inside an
async handler stalls the event loop, and what a race on a shared row looks like.

### 6. Docker and environment-based configuration
Run Postgres in a container, read a `Dockerfile`, understand a multi-stage
build, know that config comes from env vars with defaults
(`${PORT:8080}`, `${GEMINI_API_KEY:}`) and not from edited source files.

### 7. Reading long, unfamiliar code without rewriting it
`DocumentGeneratorService.java` is ~2,300 lines; `TenderController.java` ~1,000;
`AISpecificationIntelligenceService.java` ~1,100. NoticeDesk has 17 sequential
migrations that must be understood in order. The first instinct of "this is
messy, let me refactor it" is the single most expensive intern failure mode
here. Read, trace, change the minimum.

### 8. Working with LLM APIs — with the right suspicion
Both products put a model in the critical path. An intern must understand
tokens and context limits, why output is chunked, prompt versioning, temperature
and non-determinism, cost per call, and — most importantly — that **model output
is never trusted raw**. NoticeDesk validates and sanitises every field the model
returns (`app/agents/document_parsing._sanitize`); ADR-0005 spells out why.
"The model said so" is not a correctness argument.

### 9. Indian business context
Both products are built for Indian firms and Indian government systems. Interns
need working familiarity with PAN and GSTIN formats, the ₹ lakh/crore
convention, `DD/MM/YYYY` dates, IST (`Asia/Kolkata`) as the operative timezone,
and the fact that data residency is deliberate — NoticeDesk's Terraform targets
AWS Mumbai.

---

## Tier 1 — NoticeDesk-specific

### Stack to be productive in
- **FastAPI** — routers, dependency injection, middleware, Pydantic v2 models,
  `pydantic-settings` for config.
- **SQLAlchemy 2.0 async + asyncpg** — used mostly as a connection/session layer
  for hand-written SQL, not as an ORM.
- **PostgreSQL 16** — plus PL/pgSQL, because invariants are enforced by triggers.
- **Next.js 14 App Router** — server components, route handlers under
  `apps/web/app/api/*` acting as a BFF proxy to FastAPI, Tailwind with the
  project's design tokens (navy/white/slate/gold — no ad-hoc colours).
- **npm workspaces monorepo** — `apps/web`, `apps/api`, `packages/db`,
  `packages/shared`, `packages/agents`, `infra`.
- **Tooling that gates CI:** `ruff` (line length 100, rule sets E/F/W/I/B/UP/N/ASYNC),
  `mypy --strict`, `pytest`, `next lint --max-warnings=0`, `tsc --noEmit`,
  `terraform fmt -check`. A PR that fails any of these is not reviewable.
- **Nice to have, not entry-level:** Temporal (`WORKFLOW_BACKEND=temporal`),
  Terraform, AWS (RDS/S3/SES), Spring Boot for the `noticedesk-java` port.

### Concepts that must be understood before the first PR

**PAN-centric identity.** PAN is the canonical client identifier. One client has
exactly one IT registration (`identifier_value = pan`) and zero-to-many GST
registrations (GSTIN positions 3–12 = the client's PAN). Every notice, matter,
draft and intelligence row resolves to a `(client_id, registration_id)` pair —
never a bare PAN or GSTIN string. Read `docs/adr/0001` and
`packages/db/migrations/0003_clients_registrations.sql` first.

**Multi-tenancy via Row-Level Security.** Twelve tables run `FORCE ROW LEVEL
SECURITY`; every request sets `SET LOCAL app.current_tenant` in
`TenantContextMiddleware`. Forget it and queries return zero rows — which is the
*designed* failure mode, and an intern must recognise "empty result" as "tenant
context missing" rather than "data missing". Read `docs/adr/0002` and
`migrations/0009`.

**Migrations are forward-only, numbered, hand-written SQL.** No Alembic. New
schema means a new `00NN_*.sql` file plus a matching test in
`packages/db/tests/`. Never edit an applied migration.

**Vendor abstraction.** LLM, OCR, storage, email and portal connectors each sit
behind an interface + factory + stub (`app/services/llm/`, `ocr/`, `storage/`,
`email/`). Default config is stubs so CI and local dev need no API keys.
Interns must add providers behind the interface and must never import a vendor
SDK directly into a route or agent. See ADR-0003 and ADR-0005.

**Agent shape: LLM-as-tool, rules-as-router.** Document parsing is LLM-driven
with a versioned prompt file and a strict sanitiser. Notice *routing* — deciding
which client a confidential tax notice belongs to — is deliberately rule-based
with **no LLM**. Do not "improve" routing by adding a model to it.

**RBAC.** Roles are `partner`, `managing_partner`, `manager`, `staff`, `client`.
Auth is Clerk JWT, or a dev bypass (`X-Dev-User-Id` / `X-Dev-Tenant-Id`) that is
rejected unless `ENVIRONMENT=development`.

### Domain knowledge to acquire in week 1
Indian income tax and GST notices: what a notice is, common types
(ASMT-10, scrutiny and assessment notices, show-cause notices), what a due date
and a limitation period mean, why a missed deadline is a client-harming event,
and what a "matter" and a "draft reply" are in a CA firm's workflow. The
partner-facing vocabulary in the UI is the firm's vocabulary — get it wrong and
the feature is wrong even if the code is right.

---

## Tier 2 — Tender Pocket-specific

### Stack to be productive in
- **Spring Boot 3.4 / Java 21** — `@RestController`, `@Service`, `@Repository`,
  constructor and field injection, `@Value` config binding, `@Scheduled`
  (including cron with `zone = "Asia/Kolkata"`).
- **Spring Data JPA + Hibernate 6** — entities, repositories, derived query
  methods, indexes declared on `@Table`.
- **Spring Security + JWT** (jjwt 0.12.6) — filter chain, custom
  `JwtRequestFilter`, stateless auth.
- **Jsoup + HTTP clients** (`RestTemplate` and `java.net.http.HttpClient`) —
  the GeM scraper manages cookies and a CSRF hash by hand, so an intern needs to
  be comfortable in browser devtools reading real request/response traffic.
- **Document generation** — Apache POI for DOCX, OpenHTMLtoPDF/PDFBox for PDF,
  Tesseract for OCR of scanned specification PDFs (installed in the Docker image).
- **Gemini API** — chunked extraction bounded by an 8,192-token output cap, plus
  vision calls on raw file bytes.
- **Jakarta Mail** — IMAP inbox sync with a sender filter, SMTP alerts over SSL:465.
- **Deployment** — multi-stage Docker, `docker-compose`, Render (`render.yaml`).
- **Frontend** — Next.js 16 / React 19 / Tailwind 4 in the `tender-pocket` repo;
  the Spring app serves the *built* output from `src/main/resources/static` with
  a SPA forwarding controller. Interns must understand that editing files under
  `static/` is editing build output, not source.

### Sharp edges to internalise before the first ticket
- **`spring.jpa.hibernate.ddl-auto=update`** — the schema follows the entity
  classes. Changing a field type or dropping a column has real consequences on a
  live database, and there is no migration tool to catch it. Contrast this with
  NoticeDesk's explicit migrations; interns working across both must not carry
  habits from one into the other.
- **`spring.jackson.property-naming-strategy=SNAKE_CASE`** — Java camelCase
  fields serialise as `snake_case` JSON. Renaming a field is an API contract change.
- **`spring.jpa.open-in-view=false`** — no lazy loading outside a transaction.
- **Scraping is against a live third-party government portal.** It breaks when
  GeM changes markup, it must be rate-respectful, and it must never be run in a
  tight loop during development. Failures are expected and handled, not exceptional.
- **Scheduled sync runs 15s after boot, every 6 hours, and daily at 08:00 IST**,
  touching email sync, GeM scraping, and the alert engine. An intern debugging
  locally will trigger real outbound email and real portal traffic unless
  credentials are deliberately left unset.
- **`scripts/` is a working scratch area** of mixed `.ts`, `.js` and `.py`
  one-off tools. It is not a supported CLI; do not treat it as reference-quality code.

### Domain knowledge to acquire in week 1
GeM (Government e-Marketplace) and the public tender lifecycle: bid vs. tender,
EMD (earnest money deposit), document fee, corrigendum, pre-bid meeting, opening
date vs. due date, technical specification compliance, and the internal
workflow the `tenders` table models — MIS executive assignment, EMD payment
status, spec verification, submission, and outcome. The status fields on
`Tender` *are* the business process; learn the process before changing the fields.

---

## Readiness checklist

An intern is ready for a first ticket when they can do all of these unaided.

**Both projects**
- [ ] Clone, branch, commit, push, open a PR that passes CI.
- [ ] Run Postgres locally in Docker and connect with `psql`.
- [ ] Explain what an env var is doing in the config file they're editing.
- [ ] Trace one HTTP request from the browser through to the SQL it produces.

**NoticeDesk**
- [ ] `make ci-local` green on a clean checkout (db tests + api tests + web build).
- [ ] Explain, without notes, why a query returned zero rows when
      `app.current_tenant` is unset.
- [ ] Draw the PAN → IT/GST registration → matter → notice → draft chain.
- [ ] Add a trivial column: new migration file, matching schema test, updated
      route, `ruff` + `mypy --strict` + `pytest` all clean.
- [ ] Point to where the LLM's output is validated and name two things the
      sanitiser rejects.

**Tender Pocket**
- [ ] `mvn package` and run the JAR against a local Postgres.
- [ ] Build and run the Docker image; explain each stage of the Dockerfile.
- [ ] Add a field to `Tender` end-to-end (entity → repository → controller → JSON),
      and state correctly what its JSON key will be.
- [ ] Explain what happens when GeM changes its HTML, and where that breaks.
- [ ] Run the app with mail/IMAP credentials unset and explain what the
      scheduler does then.

---

## Suggested ramp (10 working days)

| Days | NoticeDesk | Tender Pocket |
|---|---|---|
| 1–2 | Read `README.md`, `docs/architecture.md`, ADRs 0001–0005 | Read `pom.xml`, `application.properties`, `Dockerfile`, `SyncScheduler` |
| 3–4 | Get local Postgres + migrations + API + web running; `make ci-local` | Build and run locally; walk one tender end-to-end in the UI |
| 5–6 | Read migrations 0001–0017 in order; write a query against the demo seed | Read `Tender.java` field by field and map each to the business process |
| 7–8 | Trace one document from upload → OCR → parse → route → draft | Trace `GeMScraperService` → `TenderRepository` → `TenderController` |
| 9–10 | Ship a small, scoped PR | Ship a small, scoped PR |

## Access to arrange before day 1
GitHub access to the relevant repos; a local Postgres; a non-production database
they can freely reset; sandbox or clearly-labelled test credentials for the LLM
providers (Anthropic/OpenAI for NoticeDesk, Gemini for Tender Pocket) with spend
caps; and — deliberately — **no** production mail, IMAP, or AWS credentials
until they have shipped supervised work.

## What interns are explicitly not expected to know on day 1
Temporal, Terraform/AWS, OCR vendor SDKs (Google Document AI, Azure Document
Intelligence), Clerk internals, the Java port of NoticeDesk, ProGuard, and
Render deployment. These are learn-on-the-job; nobody should be screened out for
them.
