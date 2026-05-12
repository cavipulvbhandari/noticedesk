"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { YearGroup } from "@/components/clients/year-group";
import { Button } from "@/components/ui/button";
import { InfoModal } from "@/components/ui/info-modal";
import {
  fetchClient,
  fetchRegistrationNotices,
  type ClientDetail,
  type RegistrationNoticesResponse,
} from "@/lib/api";

interface Props {
  params: { id: string; regId: string };
}

export default function ClientGstDrilldownPage({ params }: Props) {
  const router = useRouter();
  const [client, setClient] = useState<ClientDetail | null>(null);
  const [data, setData] = useState<RegistrationNoticesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [syncInfo, setSyncInfo] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [c, n] = await Promise.all([
          fetchClient(params.id),
          fetchRegistrationNotices(params.regId),
        ]);
        if (cancelled) return;
        setClient(c);
        setData(n);
      } catch (e: unknown) {
        if (!cancelled) setError(e instanceof Error ? e.message : "failed to load");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [params.id, params.regId]);

  if (loading) {
    return (
      <main className="mx-auto max-w-[1400px] px-10 py-8">
        <p className="py-12 text-center font-serif italic text-slate">Loading notices…</p>
      </main>
    );
  }

  if (error || !data || !client) {
    return (
      <main className="mx-auto max-w-[1400px] px-10 py-8">
        <p className="rounded border border-alarm/30 bg-alarm-bg px-3 py-2 text-sm text-alarm">
          {error ?? "Not found"}
        </p>
      </main>
    );
  }

  const reg = data.registration;
  const isPortal = reg.sync_method === "portal";

  const buckets: Record<string, typeof data.notices> = {};
  for (const n of data.notices) {
    const key = n.financial_year ?? "No FY";
    if (!buckets[key]) buckets[key] = [];
    buckets[key].push(n);
  }
  const years = Object.keys(buckets).sort().reverse();

  return (
    <main className="mx-auto max-w-[1400px] px-10 py-8 pb-16">
      <nav className="mb-3.5 flex items-center gap-2 text-[11px] font-medium uppercase tracking-[0.08em] text-slate">
        <a className="cursor-pointer hover:text-ink" onClick={() => router.push("/clients")}>
          Clients
        </a>
        <span className="text-slate-pale">›</span>
        <a
          className="cursor-pointer hover:text-ink"
          onClick={() => router.push(`/clients/${params.id}`)}
        >
          {client.legal_name}
        </a>
        <span className="text-slate-pale">›</span>
        <span>GST</span>
        <span className="text-slate-pale">›</span>
        <span className="font-semibold text-ink">
          {reg.state_name ?? reg.state_code} ({reg.identifier_value})
        </span>
      </nav>

      <header className="mb-7 flex flex-wrap items-end justify-between gap-6">
        <div>
          <h1 className="font-serif text-[36px] font-medium tracking-tight text-navy-deep">
            GST · {reg.state_name ?? reg.state_code}
          </h1>
          <p className="mt-1 font-serif text-[17px] italic text-slate">
            {client.legal_name} · GSTIN{" "}
            <span className="font-mono text-[15px]">{reg.identifier_value}</span> ·{" "}
            {data.notices.length} {data.notices.length === 1 ? "notice" : "notices"} across{" "}
            {years.length} {years.length === 1 ? "year" : "years"}
          </p>
        </div>
        <div className="flex flex-col items-end gap-2">
          <span className="flex items-center gap-2 text-[11.5px] text-slate">
            <span
              className={`h-1.5 w-1.5 rounded-full ${isPortal ? "bg-success" : "bg-slate-pale"}`}
            />
            {isPortal ? "Connected to GST portal" : "Not connected to GST portal"}
          </span>
          <Button variant="ghost" size="sm" onClick={() => setSyncInfo(true)}>
            {isPortal ? "⟲ Sync now" : "⚡ Connect portal"}
          </Button>
        </div>
      </header>

      {years.length === 0 ? (
        <div className="rounded-md border border-dashed border-slate-line bg-white p-10 text-center">
          <p className="font-serif text-[16px] text-navy-deep">No notices yet</p>
          <p className="mt-1 text-sm text-slate">
            Upload a GST notice for this state to start a record here.
          </p>
        </div>
      ) : (
        years.map((fy) => (
          <YearGroup
            key={fy}
            title={fy === "No FY" ? "No financial year" : `Financial Year ${fy}`}
            notices={buckets[fy]!}
          />
        ))
      )}

      <InfoModal
        open={syncInfo}
        title="Portal sync arrives in Phase 2"
        eyebrow="Coming soon"
        onClose={() => setSyncInfo(false)}
      >
        <p className="mb-3">
          We&rsquo;ll connect {reg.identifier_value} to the GST GSP so new
          notices arrive in the inbox automatically and replies file straight
          from NoticeDesk.
        </p>
        <p className="text-slate">
          For Phase 1, drop scanned PDFs into the inbox or forward emails to
          your firm&rsquo;s ingestion address.
        </p>
      </InfoModal>
    </main>
  );
}
