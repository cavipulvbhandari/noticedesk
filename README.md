# NoticeDesk

Litigation-first tax operating system for Indian CA firms. Sprint 1: foundation scaffold (PAN-centric data model, auth, API, frontend skeleton).

## Repository layout

```
/apps
  /web        Next.js 14 App Router frontend
  /api        FastAPI backend (Python 3.11+)
/packages
  /db         PostgreSQL migrations and schema
  /shared     TypeScript types shared between web and api
  /agents     Python agent prompts and orchestration (placeholder for V2 sprints)
/infra        Terraform for AWS Mumbai
/docs         Architecture decision records
```

## Identity model (non-negotiable)

PAN is the canonical identifier for every client. A client has exactly one IT
registration (`identifier_value = pan`) and zero-to-many GST registrations
(GSTIN where positions 3-12 = the client's PAN). Every notice, matter, draft,
and intelligence output resolves to a `(client_id, registration_id)` pair.

See `docs/adr/0001-pan-centric-identity-model.md`.

## Sprint 1 scope

This sprint produces no end-user features. It produces a deployable skeleton
that subsequent sprints build on top of. Notice parsing, drafting, reminders,
WhatsApp, and any agent functionality are explicitly out of scope.

## Local development

See `apps/api/README.md` and `apps/web/README.md`.

## Branch / deploy

- Feature branch: `claude/noticedesk-sprint-1-foundation-Xyr0t`
- CI: `.github/workflows/ci.yml`
