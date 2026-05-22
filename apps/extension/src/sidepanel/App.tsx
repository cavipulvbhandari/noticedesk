import { useEffect, useState } from 'react';
import { strings } from '@/shared/strings';

type ActiveHost = { status: 'loading' } | { status: 'ok'; host: string } | { status: 'offPortal' };

const GST_HOST_SUFFIX = '.gst.gov.in';

function readActiveTabHost(): Promise<ActiveHost> {
  return new Promise((resolve) => {
    if (!chrome?.tabs?.query) {
      resolve({ status: 'offPortal' });
      return;
    }
    chrome.tabs.query({ active: true, lastFocusedWindow: true }, (tabs) => {
      const url = tabs[0]?.url ?? '';
      try {
        const host = new URL(url).hostname;
        if (host === 'gst.gov.in' || host.endsWith(GST_HOST_SUFFIX)) {
          resolve({ status: 'ok', host });
          return;
        }
      } catch {
        /* fall through */
      }
      resolve({ status: 'offPortal' });
    });
  });
}

export function App(): JSX.Element {
  const [active, setActive] = useState<ActiveHost>({ status: 'loading' });

  useEffect(() => {
    void readActiveTabHost().then(setActive);
    const handler = (): void => {
      void readActiveTabHost().then(setActive);
    };
    chrome.tabs?.onActivated.addListener(handler);
    chrome.tabs?.onUpdated.addListener(handler);
    return () => {
      chrome.tabs?.onActivated.removeListener(handler);
      chrome.tabs?.onUpdated.removeListener(handler);
    };
  }, []);

  return (
    <main className="flex h-full flex-col gap-4 p-4">
      <header className="border-b border-slate-200 pb-3">
        <h1 className="text-lg font-semibold text-brand-700">{strings.appName}</h1>
        <p className="text-xs text-slate-500">{strings.appTagline}</p>
      </header>

      <section
        aria-live="polite"
        className="rounded-md border border-slate-200 bg-white p-3 text-sm"
      >
        {active.status === 'loading' && (
          <p className="text-slate-500">{strings.status.loading}</p>
        )}
        {active.status === 'ok' && (
          <p className="text-slate-700">
            <span className="font-medium text-emerald-700">●</span> {strings.status.onPortal}{' '}
            <code className="rounded bg-slate-100 px-1 py-0.5 text-xs">{active.host}</code>
          </p>
        )}
        {active.status === 'offPortal' && (
          <p className="text-slate-600">
            <span className="font-medium text-amber-600">●</span> {strings.status.offPortal}
          </p>
        )}
      </section>

      <section className="rounded-md border border-dashed border-slate-300 bg-white p-3 text-xs text-slate-500">
        <p className="mb-1 font-medium text-slate-700">{strings.phase1.heading}</p>
        <p>{strings.phase1.body}</p>
      </section>

      <footer className="mt-auto text-[10px] text-slate-400">{strings.footer}</footer>
    </main>
  );
}
