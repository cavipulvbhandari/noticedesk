# NoticeDesk Chrome Extension

A module of **NoticeDesk by Litigence** — automates collection of statutory
communications from `incometax.gov.in` and `gst.gov.in` while the
practitioner (CA / AR / Advocate) is logged in to their own or their client's
account.

> **Phase 1 — Scaffold checkpoint.** This commit contains *only* the build
> pipeline and an empty side panel scoped to `gst.gov.in`. No scrapers, no
> downloads, no off-portal HTTP requests. See
> `docs/NoticeDesk_Chrome_Extension_ClaudeCode_Prompt1.md` §9 for the phased
> delivery plan.

## Tech stack

- Manifest V3
- Vite + `@crxjs/vite-plugin`
- React 18 + Tailwind CSS in the side panel
- TypeScript **strict** (`noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`)
- Dexie (IndexedDB) for the local notice register

## Hard constraints (non-negotiable)

The extension operates only within the user's authenticated session and only
on data they are already entitled to view as the logged-in user or mapped AR.

- **No** credential harvesting
- **No** headless re-login
- **No** captcha bypass
- **No** scraping of any other user's data
- **No** off-portal HTTP requests to either portal

See `COMPLIANCE.md` (Phase 1 deliverable, forthcoming) for the full
DPDP / ICAI / BCI mapping.

## Local development

```bash
# from the monorepo root
npm install
npm --workspace @noticedesk/extension run build       # produces dist/
npm --workspace @noticedesk/extension run typecheck   # strict TS check
npm --workspace @noticedesk/extension run dev         # vite dev server with HMR
```

### Load the unpacked extension

1. `npm --workspace @noticedesk/extension run build`
2. Chrome → `chrome://extensions` → Developer mode → **Load unpacked**
3. Point at `apps/extension/dist/`
4. Visit `https://services.gst.gov.in/services/login` (or any `*.gst.gov.in`
   page) and click the NoticeDesk toolbar icon. The side panel should open.
5. On any non-GST tab the toolbar icon stays inactive — the side panel is
   disabled for that tab by the background service worker.

## Layout

```
apps/extension/
├── manifest.config.ts        # Manifest V3 (CRXJS defineManifest)
├── vite.config.ts            # Vite + CRXJS + React
├── tailwind.config.ts
├── tsconfig.json             # strict mode
└── src/
    ├── background/           # service worker — side-panel gating only (Phase 1)
    ├── content/              # (Phase 2+) DOM observers
    │   ├── incometax/
    │   └── gst/
    ├── sidepanel/            # React side-panel UI
    ├── options/              # (Phase 3) settings page
    ├── lib/
    │   ├── classifiers/      # (Phase 2+) Form/Section → category mapping
    │   ├── parsers/          # (Phase 2+) PAN/GSTIN/AY/DIN regexes
    │   ├── storage/          # Dexie schema (skeleton only in Phase 1)
    │   └── api/              # (Phase 3) NoticeDesk backend client
    └── shared/               # cross-context types, strings, constants
```

## Phase roadmap

| Phase | Scope | Status |
| ----- | ----- | ------ |
| 1     | Scaffold, empty side panel on gst.gov.in only | **in progress** |
| 2     | GST scrapers (View Notices and Orders + View Additional Notices/Orders), register, XLSX export | not started |
| 3     | Income Tax parity (e-Proceedings, AR multi-PAN, Outstanding Demand) | not started |
| 4     | Backend sync + multi-client orchestration | not started |
| 5     | (scope-out) PDF text extraction — documented only | not in engagement |
