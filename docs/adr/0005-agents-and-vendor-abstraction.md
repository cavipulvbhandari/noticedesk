# ADR-0005 — Agent shape: LLM-as-tool, rules-as-router

- Status: Accepted
- Date: 2026-05-12
- Authors: Anuthi Bhansali, Vipul Bhandari

## Context

Sprint 3 introduces the first two agents in the system: a Document Parsing
Agent (classifies a notice and extracts structured fields) and a Notice
Routing Agent (places the parsed notice under the right client and
registration). Both run sequentially after Sprint 2's OCR pipeline.

We had to decide for each agent what kind of agent it is — LLM-driven,
rule-based, or something else — and how its vendor dependency, if any, is
abstracted. Getting this split wrong would either bake an LLM into routing
logic where determinism matters most, or force us to maintain a brittle
regex extractor across every notice variant Indian tax authorities publish.

## Decision

**Document Parsing Agent — LLM-driven, behind an abstraction layer.**

Classifying eight notice types and extracting twenty-odd fields out of OCR
text varies wildly across authorities, layouts, and OCR quality. We use
Claude (primary; `claude-opus-4-7`) with OpenAI as fallback, behind an
`LLMProvider` interface that follows the same vendor-abstraction pattern
as `OCRProvider` and `Storage`. The prompt lives in a versioned file
(`prompts/document_parsing_v1.md`) and the version is recorded on every
audit row, so we can replay any historical run. The agent's output is
strictly JSON; a sanitiser in `app.agents.document_parsing._sanitize`
validates every field, drops fabricated identifiers, normalises Indian
date formats, and snaps the law field to whatever the document type
implies. **We never trust the LLM's raw output.**

**Notice Routing Agent — rule-based, no LLM.**

Routing decides which client and which registration a notice belongs to.
This is the most safety-critical step in the entire system: a wrong
routing call sends a confidential tax notice to the wrong firm. LLM
non-determinism is exactly what we don't want here. The five-step
procedure (PAN canonicalisation → client lookup → registration lookup →
matter match-or-create → notice insert) is pure rule-based Python with no
model in the loop. The PAN/GSTIN reconciliation check (`pan_gstin_mismatch`)
is structurally enforced both in Step A and at the database trigger from
ADR-0001 — two independent layers blocking a mis-route.

The two agents share an audit-log contract: every step emits an
`audit_logs` row with prompt version, model, and confidence, so the next
sprints (drafting, citation verification) inherit the same provenance
trail.

## Consequences

- Adding a new LLM provider is a config flag + one file
  (`app/services/llm/<vendor>.py`). The agent itself never touches a
  vendor SDK.
- Adding a new notice type is a prompt-v2 update plus a new entry in
  `KNOWN_DOCUMENT_TYPES`. Routing logic is unchanged.
- A bad prompt update can't silently route documents wrong: the rule-based
  router's Step A still blocks PAN/GSTIN mismatches even if the parser
  hallucinated identifiers, and the sanitiser drops every hallucinated
  PAN before it reaches the router.
- The same `_match_or_create_matter` helper used by automatic routing is
  reused by the manual-override endpoint, so the matter graph stays
  consistent regardless of how a notice was attached.
- The eval suite in `app/agents/evals/` has two modes: `--mode=real`
  (calls the actual LLM, costs money, used when tuning prompts) and
  `--mode=regex` (deterministic, runs in CI, exercises the surrounding
  plumbing).

## Alternatives considered

- **LLM in routing.** Rejected — non-determinism on the most
  safety-critical step is not acceptable for V1.
- **Pure regex parsing, no LLM.** Rejected — Indian tax notice layouts
  are too heterogeneous and would require per-authority extractors we
  don't have time to maintain.
- **Function-calling / structured output through a single vendor SDK.**
  Tempting but locks us into one vendor. We keep the abstraction layer
  and parse JSON from the model's response.

## Future work

- Once Sprint 5 introduces the Drafting Agent, this same pattern (LLM
  behind a provider abstraction, sanitiser, audit trail) carries over.
- Prompt versions become a first-class deployable artifact; we may add
  a `prompts/` migration step that loads them into S3 alongside code.
