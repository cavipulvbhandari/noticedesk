# ADR-0001 — PAN-centric identity model

- Status: Accepted
- Date: 2026-05-08
- Authors: Vipul Bhandari, Anuthi Bhansali

## Context

Every Indian taxpayer has exactly one Permanent Account Number (PAN). Income
Tax records are keyed directly to the PAN. Goods and Services Tax records are
keyed to a 15-character GSTIN, but positions 3-12 of every GSTIN are
deterministically the entity's PAN. A taxpayer with operations in multiple
states therefore has one PAN and many GSTINs that all share the same embedded
PAN. We need a data model that lets a CA firm see all of a client's tax
litigation — IT and GST, across every state — under a single canonical
identity.

We considered three alternatives:

1. **Bare PAN/GSTIN strings on every row.** Smallest schema. Forces every
   query to do string parsing and reconciliation, and makes it trivial to
   route a notice to a different client whose PAN happens to match the
   GSTIN. Rejected.
2. **Client + state-scoped registration as separate roots.** Treat IT and
   GST as parallel hierarchies. Loses the consolidated view we need for
   cross-adjudication risk and partner-level dashboards. Rejected.
3. **PAN-keyed client with one IT registration and zero-to-many GST
   registrations** (this ADR).

## Decision

`clients` is keyed by `(tenant_id, pan)`. Every client has exactly one IT
registration whose `identifier_value` equals the PAN, and zero-to-many GST
registrations whose `identifier_value` is the 15-character GSTIN with
`identifier_value[3:12] = pan`.

Every notice, matter, draft, and intelligence output resolves to a
`(client_id, registration_id)` pair. The denormalized `client_id` column on
`notices` and `matters` exists so partner-level firm-wide queries don't have
to join through `client_registrations` on hot paths.

The PAN consistency is enforced at three layers:

1. CHECK constraints on PAN/GSTIN format.
2. A trigger on `client_registrations` that compares
   `client.pan` against either `identifier_value` (IT) or
   `SUBSTRING(identifier_value, 3, 10)` (GST).
3. A unique partial index that allows at most one `'IT'` row per client.

Application code reuses the same rule via
`apps/api/app/services/identity.py::reconcile_pan_gstin` whenever a notice is
ingested. A mismatch is a hard error, not a default.

## Consequences

- A notice cannot silently be attached to a different client even if the
  PAN/GSTIN happen to overlap by accident — the trigger is a structural gate.
- Cross-adjudication queries (e.g. "if we admit X in this GST reply, does
  it open up an IT exposure for the same client across any AY?") are a
  single client_id join.
- Group structures (holding/subsidiary, related-party) are explicitly
  *not* the canonical identity. They live in `clients.group_relationships`
  as a soft graph and never bypass the PAN gate.
- Adding adjacent regulators in V2+ (PMLA, FEMA, Customs, etc.) will require
  a new `registration_type` value and a new trigger branch. This is the
  point — the identity model is the extension surface.

## Alternatives considered

See "Context" above.
