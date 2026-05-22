# NoticeDesk Chrome Extension — Claude Code Implementation Prompt

## 1. Project Context

You are building a Chrome extension as a module of **NoticeDesk by Litigence**, an AI-powered platform for Indian tax-controversy and litigation management. The extension automates collection of statutory communications from `incometax.gov.in` and `gst.gov.in` while the practitioner (Chartered Accountant / Authorised Representative / Advocate) is logged in to their own or their client's account through the AR dashboard.

**Primary users:** CA firms, tax counsel, and corporate tax teams who currently spend significant time manually downloading PDFs across many PANs/GSTINs.

**Hard constraint — non-negotiable:** The extension operates *only* within the user's authenticated session and *only* on data the user is already entitled to view as the logged-in user or mapped AR. There must be **no** credential harvesting, **no** headless re-login, **no** captcha bypass, **no** scraping of any other user's data, and **no** off-portal HTTP requests to either portal.

## 2. Tech Stack

- Chrome Extension **Manifest V3**
- Service worker (background) in TypeScript
- Content scripts in TypeScript bundled via Vite + `@crxjs/vite-plugin`
- UI: React 18 + Tailwind CSS in `chrome.sidePanel` and the options page
- Storage: `chrome.storage.local` for settings, `chrome.downloads` for files, IndexedDB via **Dexie** for the local notice register
- Optional backend sync: REST POST to NoticeDesk API (configurable endpoint + bearer token in options page)
- XLSX export via SheetJS
- Lint: ESLint + Prettier; tests: Vitest unit + Playwright E2E
- TypeScript **strict mode**

## 3. High-Level Architecture

```
extension/
├── manifest.json
├── src/
│   ├── background/         service worker, download orchestration, sync queue
│   ├── content/
│   │   ├── incometax/      DOM observers + extractors for incometax.gov.in
│   │   └── gst/            DOM observers + extractors for gst.gov.in
│   ├── sidepanel/          React UI: dashboard, queue, register, sync
│   ├── options/            settings, API endpoint, token, client mapping
│   ├── lib/
│   │   ├── classifiers/    rule-based mapping Notice/Order/Reply + Section/Form
│   │   ├── parsers/        AY/FY, PAN, GSTIN, ARN, DIN, section, form code
│   │   ├── storage/        Dexie schemas, migrations
│   │   └── api/            NoticeDesk backend client
│   └── shared/             types, message protocol, constants
└── tests/
```

All DOM selectors live in one `selectors.ts` per portal — portal UI changes must require a single-file fix. All user-visible strings in `strings.ts` to allow Hindi/Marathi localisation later.

## 4. Portal-Specific Scraping Requirements

### 4.1 incometax.gov.in

Detect and capture from:

- **Dashboard → Pending Actions / For Your Action** — open notices summary
- **e-File → Income Tax Returns → e-Proceedings** — the canonical workflow for assessment, reassessment, penalty, rectification, and faceless proceedings (NFAC)
- **e-File → e-Pay Tax → Outstanding Demand** — demand notices u/s 156
- **Pending Actions → Worklist / Compliance Portal** — high-value information notices
- **Authorised Representative dashboard** — list of mapped PANs (treat each PAN as a separate `Client` record)
- **e-Proceedings → Response History** — replies/submissions filed by the assessee/AR

For each item extract: PAN, AY, DIN (Document Identification Number), Section (`143(1)`, `143(2)`, `142(1)`, `148`, `148A(b)`, `148A(d)`, `156`, `250`, `271AAC`, `270A`, `271(1)(c)`, etc.), Date of Issue, Response Due Date, Notice Type (Notice / Intimation / Order / Reply Filed / Submission), Proceeding Reference Number, attached PDF URL(s).

### 4.2 gst.gov.in

Detect and capture from:

- **Services → User Services → View Notices and Orders**
- **Services → User Services → View Additional Notices/Orders** *(explicitly scrape this — practitioners most often miss it)*
- **Services → Refunds → Track Application Status** — RFD-08 SCNs, RFD-06 sanction/rejection orders
- **Services → User Services → My Applications** — ARN-wise replies filed
- **Dashboard → View Notices and Orders** widget
- **Services → User Services → My Applications → Appeals** — APL-01/02/03/04 trail

For each item extract: GSTIN, Legal Name, Trade Name, Tax Period(s), Form Type (`DRC-01`, `DRC-01A`, `DRC-07`, `DRC-08`, `ASMT-10`, `ASMT-13`, `REG-17`, `REG-19`, `RFD-08`, `APL-02`, `APL-04`, etc.), Section (`73`, `74`, `74A`, `61`, `65`, `67`, `129`, etc.), Reference Number (SCN/Order Ref. No.), Date of Issue, Reply Due Date, Status (Issued / Reply Filed / Closed / Appealed), attached PDF URL(s), ARN of any reply filed.

### 4.3 Common scraping rules

- **Never** trigger or bypass a captcha. If a captcha appears in the DOM, halt for that page and show a sidepanel toast asking the user to solve it manually.
- Add jitter of 800–1500 ms between any page navigations the extension itself initiates.
- The extension may navigate on behalf of the user **only** when the user has clicked "Sync this client" or "Sync all". No autonomous navigation otherwise.
- Files are downloaded via `chrome.downloads.download` to:
  `NoticeDesk/{PAN-or-GSTIN}/{AY-or-Period}/{FormOrSection}_{DIN-or-RefNo}.pdf`

## 5. Data Model (Dexie / IndexedDB)

```ts
interface Client {
  id: string;                 // UUID
  type: 'IT' | 'GST';
  identifier: string;         // PAN or GSTIN
  legalName: string;
  tradeName?: string;
  lastSyncedAt?: number;
}

interface NoticeRecord {
  id: string;
  clientId: string;
  portal: 'IT' | 'GST';
  category: 'Notice' | 'Intimation' | 'Order' | 'Reply' | 'Submission';
  formOrSection: string;      // 'DRC-01' | '143(2)' | etc.
  referenceNumber: string;    // DIN / SCN Ref / ARN
  taxPeriod: string;          // 'AY 2018-19' or 'Apr 2023 – Jun 2023'
  issuedOn: string;           // ISO date
  dueOn?: string;
  status: string;
  sourceUrl: string;
  localFilePath?: string;
  capturedAt: number;
  syncedAt?: number;
  rawDom?: string;            // optional, opt-in, diagnostics only
}
```

Idempotency key: `(portal, referenceNumber)` — never duplicate on re-sync.

## 6. Classification & Parsing

In `lib/classifiers/` build a rule-based mapper:

- Every known GST Form code (`DRC-01`, `DRC-01A`, `DRC-07`, `DRC-08`, `ASMT-10`, `ASMT-13`, `RFD-08`, `APL-02`, `APL-04`, `REG-17`, `REG-19` …) → stable category + human label.
- Every IT section (`143(1)`, `143(2)`, `142(1)`, `148`, `148A(b)`, `148A(d)`, `156`, `250`, `270A`, `271AAC`, `271(1)(c)`) → category + label.
- Tolerant regex module for AY/FY parsing across formats: "A.Y. 2018-19", "AY 2018-2019", "FY 2023-24", "Tax Period: Apr 2023 – Jun 2023".
- Validate PAN `^[A-Z]{5}[0-9]{4}[A-Z]$` and GSTIN (15 chars: state code + PAN + entity + Z + checksum). Reject malformed identifiers from being persisted.

## 7. Sidepanel UX

- **Dashboard** — client list, last sync time, pending notices count, action-required count (items due within 7 days highlighted in red).
- **Queue** — live per-item scrape progress.
- **Register** — searchable, filterable table; columns: Client, Portal, Category, Form/Section, Ref No., Issued, Due, Status, File. One-click XLSX export.
- **Sync** — backend sync state, retry failed items.
- **Options** — API endpoint, bearer token, download folder, AR/client mapping, opt-in toggles.

## 8. Compliance & Ethics

The extension and its `COMPLIANCE.md` must document conformance with:

- **DPDP Act, 2023** — process only data the user is authorised to view; local-first storage; explicit opt-in for backend sync; data deletion on request; no third-party analytics or trackers.
- **ICAI Code of Ethics, 13th Edition** — client confidentiality; strict segregation by PAN/GSTIN; no commingling in storage.
- **Bar Council of India Rule 36** — no solicitation copy or features inside the extension UI.
- **Portal Terms of Use** — automation limited to actions initiated by the logged-in user; no credential storage; no background re-login; no captcha bypass.

## 9. Deliverables — Phased

**Do not start a phase until the previous one is complete, tested, and committed.**

**Phase 1 — MVP (GST portal, single GSTIN, read-only register):**
- Manifest, build pipeline, sidepanel skeleton.
- Content script for `View Notices and Orders` + `View Additional Notices/Orders`.
- Metadata capture + PDF download for the logged-in GSTIN.
- Local Dexie register + XLSX export.

**Phase 2 — Income Tax parity:**
- AR dashboard detection (multi-PAN).
- e-Proceedings extractor with full reply history.
- Outstanding Demand u/s 156.

**Phase 3 — Backend sync + multi-client orchestration:**
- "Sync all clients" with rate limiting and resumability.
- NoticeDesk API client with bearer auth.
- Retry queue and idempotent conflict resolution on `(portal, referenceNumber)`.

**Phase 4 — (scope-out, document only):** PDF text extraction + structured data extraction from notice bodies (Section/AY/quantum). Not built in this engagement.

## 10. Testing

- Unit tests for every parser and classifier with a `tests/fixtures/` folder of real DOM snapshots **sanitised** — PAN replaced with `AAAAA0000A`, GSTIN with `27AAAAA0000A1Z5`, DINs/ARNs with stable dummies.
- Playwright E2E against a local mock HTML server replaying sanitised portal pages.
- `tests/fixtures/README.md` documenting how to add a new sanitised snapshot when the portals change UI.

## 11. Coding Standards

- TypeScript strict mode on; no `any`; discriminated unions for portal-specific records.
- All DOM selectors centralised per portal in `selectors.ts`.
- All user-visible strings in `strings.ts`.
- Conventional Commits; one feature per PR.

## 12. Repository Hygiene

- `README.md` with install/dev instructions, screenshots, scope of work.
- `CLAUDE.md` describing architecture for future AI-assisted edits.
- `COMPLIANCE.md` as in §8.
- `CHANGELOG.md` from day one.

---

**Begin with Phase 1, Step 1:** scaffold the Vite + CRXJS + React + Tailwind project with TypeScript strict mode and Dexie. Push an empty side panel that opens on `gst.gov.in` only. Confirm the build before writing any scraper code. Pause for review at that checkpoint.
