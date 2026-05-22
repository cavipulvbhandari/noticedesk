# CLAUDE.md — NoticeDesk Chrome Extension

Architectural guide for future AI-assisted edits. Read this before changing
anything in `apps/extension/`.

## Non-negotiable invariants

These mirror §1 and §8 of `NoticeDesk_Chrome_Extension_ClaudeCode_Prompt1.md`.
Do not relax them, even partially, without explicit user approval:

1. The extension operates **only** within the user's authenticated session.
2. **No** credential storage, headless re-login, or captcha bypass.
3. **No** off-portal HTTP requests to `incometax.gov.in` or `gst.gov.in`.
   The only outbound network call permitted is to the user-configured
   NoticeDesk backend (Phase 3+, opt-in, bearer auth).
4. Storage is local-first (Dexie + `chrome.storage.local` + `chrome.downloads`).
   Backend sync is **opt-in** in the options page.
5. Strict PAN/GSTIN segregation in storage (no commingling across clients).

## File-placement rules

- **DOM selectors** for a portal live in exactly one place:
  `src/content/<portal>/selectors.ts`. A portal UI change must be a
  single-file fix.
- **User-visible strings** live in `src/shared/strings.ts` (or
  `src/shared/strings.<locale>.ts` later). React components must not
  contain bare English strings.
- **Form/Section classifiers** live in `src/lib/classifiers/`.
- **Regex parsers** (PAN, GSTIN, AY/FY, DIN, ARN, etc.) live in
  `src/lib/parsers/` with unit tests in `tests/`.
- **Backend client** lives in `src/lib/api/` and reads endpoint + token
  from `chrome.storage.local` via the options page.

## TypeScript

`tsconfig.json` enables strict mode plus `noUncheckedIndexedAccess` and
`exactOptionalPropertyTypes`. Do not relax any compiler option to make a
change compile — fix the code instead. `any` is banned by lint rule.

Portal-specific records must use discriminated unions on `portal: 'IT' | 'GST'`.

## Idempotency

Notice writes use the compound key `[portal+referenceNumber]`. Re-syncing
the same notice must update the existing record, never duplicate.

## What Phase 1 does **not** include

- Any DOM scraping
- Any file downloads
- Any content script
- Any options page UI
- Any backend network call
- Any XLSX export

If you are asked to add any of those, you are starting Phase 2+ — confirm
with the user first and ensure prior phases are tested and committed.

## Build & checks

```bash
npm --workspace @noticedesk/extension run typecheck
npm --workspace @noticedesk/extension run lint
npm --workspace @noticedesk/extension run build
```

CI in `.github/workflows/` should run typecheck on every PR touching
`apps/extension/**`.
