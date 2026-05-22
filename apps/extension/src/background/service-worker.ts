/**
 * Background service worker — Phase 1.
 *
 * Responsibilities here are intentionally minimal:
 *  1. Open the side panel when the toolbar action is clicked.
 *  2. Enable the side panel only on gst.gov.in tabs; disable it elsewhere.
 *
 * No autonomous navigation, no scraping, no off-portal HTTP requests
 * (per §4.3 and §8 of NoticeDesk_Chrome_Extension_ClaudeCode_Prompt1.md).
 */

import { classifyHost } from '@/shared/constants';

const SIDE_PANEL_PATH = 'src/sidepanel/index.html';

chrome.runtime.onInstalled.addListener(() => {
  void chrome.sidePanel
    .setPanelBehavior({ openPanelOnActionClick: true })
    .catch((err: unknown) => console.warn('[NoticeDesk] setPanelBehavior failed', err));
});

function isGstUrl(url: string | undefined): boolean {
  if (!url) return false;
  try {
    return classifyHost(new URL(url).hostname) === 'GST';
  } catch {
    return false;
  }
}

async function syncSidePanelForTab(tabId: number, url: string | undefined): Promise<void> {
  const enabled = isGstUrl(url);
  await chrome.sidePanel.setOptions({
    tabId,
    path: SIDE_PANEL_PATH,
    enabled,
  });
}

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.url || changeInfo.status === 'loading') {
    void syncSidePanelForTab(tabId, tab.url);
  }
});

chrome.tabs.onActivated.addListener(({ tabId }) => {
  chrome.tabs.get(tabId, (tab) => {
    if (chrome.runtime.lastError) return;
    void syncSidePanelForTab(tabId, tab.url);
  });
});

export {};
