import { defineManifest } from '@crxjs/vite-plugin';
import pkg from './package.json' with { type: 'json' };

/**
 * Phase 1 manifest: read-only side panel scoped strictly to gst.gov.in.
 * No content scripts, no scrapers, no off-portal host permissions yet —
 * those land in later phases per NoticeDesk_Chrome_Extension_ClaudeCode_Prompt1.md §9.
 */
export default defineManifest({
  manifest_version: 3,
  name: 'NoticeDesk by Litigence',
  description:
    'Collect statutory communications from gst.gov.in within your authenticated session. No credential harvesting, no captcha bypass.',
  version: pkg.version,
  minimum_chrome_version: '116',
  permissions: ['sidePanel', 'storage', 'tabs', 'downloads'],
  host_permissions: ['https://*.gst.gov.in/*'],
  background: {
    service_worker: 'src/background/service-worker.ts',
    type: 'module',
  },
  action: {
    default_title: 'NoticeDesk — open side panel',
  },
  side_panel: {
    default_path: 'src/sidepanel/index.html',
  },
  icons: {
    16: 'src/icons/icon-16.png',
    32: 'src/icons/icon-32.png',
    48: 'src/icons/icon-48.png',
    128: 'src/icons/icon-128.png',
  },
});
