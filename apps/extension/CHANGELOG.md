# Changelog

All notable changes to the NoticeDesk Chrome Extension will be documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added — Phase 1 scaffold

- Vite + `@crxjs/vite-plugin` build pipeline.
- React 18 + Tailwind CSS side panel skeleton.
- TypeScript strict mode (`noUncheckedIndexedAccess`,
  `exactOptionalPropertyTypes`, `noImplicitOverride`).
- Manifest V3 with `host_permissions` restricted to `https://*.gst.gov.in/*`.
- Background service worker that enables the side panel only on
  `gst.gov.in` tabs and opens it on toolbar-action click.
- Dexie schema skeleton for `Client` and `NoticeRecord` (no writes yet).
- Compound idempotency index `[portal+referenceNumber]` per
  implementation prompt §5.
- Placeholder localisable strings module (`src/shared/strings.ts`) ready
  for Hindi/Marathi later.
