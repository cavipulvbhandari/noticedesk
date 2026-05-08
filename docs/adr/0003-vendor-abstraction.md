# ADR-0003 — Vendor abstraction at every external boundary

- Status: Accepted
- Date: 2026-05-08
- Authors: Anuthi Bhansali

## Context

The Sprint 1 stack pins specific vendors (Anthropic, OpenAI, Google Document
AI, Azure DI fallback, Gupshup/Interakt for WhatsApp, MSG91 for SMS, AWS
SES). Vendor lock-in at the call site would make migrations expensive and
make per-tenant compliance variations (e.g. an enterprise tenant insisting
on a specific LLM) impossible without a refactor.

## Decision

No module hard-codes a specific LLM, OCR, BSP, or legal-database vendor.
Every external dependency is reached through a thin interface in
`apps/api/app/services/`. Sprint 1 ships only the identity service; Sprint 2
introduces the OCR adapter and Sprint 3 introduces the LLM adapter, both
behind the same pattern.

## Consequences

- Switching a vendor is a 1-file change at the adapter boundary.
- Per-tenant overrides are a config lookup, not a code path.
- Adapters MUST run through Temporal workflows (per the architecture
  principles: "Queue-based for external calls"). Synchronous APIs are read-only.

## Alternatives considered

- Direct vendor SDK usage at the call site. Rejected.
