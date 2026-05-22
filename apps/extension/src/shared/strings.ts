/**
 * All user-visible strings live here per
 * NoticeDesk_Chrome_Extension_ClaudeCode_Prompt1.md §3 — to allow
 * Hindi/Marathi localisation later without touching components.
 */
export const strings = {
  appName: 'NoticeDesk',
  appTagline: 'by Litigence — statutory notice register',
  status: {
    loading: 'Detecting active tab…',
    onPortal: 'Connected to GST portal:',
    offPortal:
      'Open a tab on gst.gov.in to use NoticeDesk. The extension is scoped to that portal in Phase 1.',
  },
  phase1: {
    heading: 'Phase 1 — Scaffold checkpoint',
    body:
      'No scrapers, no downloads, no off-portal requests yet. This empty side panel exists only to confirm the build pipeline.',
  },
  footer: '© Litigence · Local-first · DPDP Act 2023 compliant',
} as const;
