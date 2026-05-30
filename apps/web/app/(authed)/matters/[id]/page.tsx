"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { DocumentsTab } from "@/components/matters/documents-tab";
import { DraftTab } from "@/components/matters/draft-tab";
import { MatterHeader } from "@/components/matters/matter-header";
import { MatterTabs, type MatterTab } from "@/components/matters/matter-tabs";
import { NoticeTab } from "@/components/matters/notice-tab";
import { TimelineTab } from "@/components/matters/timeline-tab";
import { TriageTab } from "@/components/matters/triage-tab";
import { useToast } from "@/components/ui/toast";
import { fetchNotice, transitionLifecycle, type NoticeDetail } from "@/lib/api";

interface Props {
  params: { id: string };
}

export default function MatterPage({ params }: Props) {
  const router = useRouter();
  const { toast } = useToast();
  const [data, setData] = useState<NoticeDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<MatterTab>("notice");

  const load = useCallback(async () => {
    try {
      const next = await fetchNotice(params.id);
      setData(next);
      setError(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "failed to load notice");
    } finally {
      setLoading(false);
    }
  }, [params.id]);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading && !data) {
    return (
      <main className="mx-auto max-w-[1400px] px-10 py-8">
        <p className="py-12 text-center font-serif italic text-slate">Loading matter…</p>
      </main>
    );
  }
  if (error || !data) {
    return (
      <main className="mx-auto max-w-[1400px] px-10 py-8">
        <p className="rounded border border-alarm/30 bg-alarm-bg px-3 py-2 text-sm text-alarm">
          {error ?? "Notice not found"}
        </p>
      </main>
    );
  }

  const { client, registration, notice } = data;

  async function handleTransition(next: string, reason: string | null) {
    const res = await transitionLifecycle(params.id, {
      lifecycle_status: next,
      ...(reason ? { reason } : {}),
    });
    if (res.changed) {
      toast(`Moved to ${next.replace(/_/g, " ")}`, "success");
      await load();
    }
  }

  return (
    <main className="mx-auto max-w-[1400px] px-10 py-8 pb-16">
      <nav className="mb-3.5 flex items-center gap-2 text-[11px] font-medium uppercase tracking-[0.08em] text-slate">
        <a className="cursor-pointer hover:text-ink" onClick={() => router.push("/clients")}>
          Clients
        </a>
        <span className="text-slate-pale">›</span>
        <a
          className="cursor-pointer hover:text-ink"
          onClick={() => router.push(`/clients/${client.client_id}`)}
        >
          {client.legal_name}
        </a>
        <span className="text-slate-pale">›</span>
        {registration.registration_type === "GST" ? (
          <>
            <a
              className="cursor-pointer hover:text-ink"
              onClick={() =>
                router.push(
                  `/clients/${client.client_id}/gst/${registration.registration_id}`,
                )
              }
            >
              GST · {registration.state_name ?? registration.state_code}
            </a>
          </>
        ) : (
          <a
            className="cursor-pointer hover:text-ink"
            onClick={() => router.push(`/clients/${client.client_id}/it`)}
          >
            Income Tax
          </a>
        )}
        <span className="text-slate-pale">›</span>
        <span className="font-semibold text-ink">
          {notice.document_type ?? notice.law}
        </span>
      </nav>

      <MatterHeader data={data} onTransition={handleTransition} />

      <MatterTabs active={tab} onChange={setTab} />

      {tab === "notice" ? <NoticeTab data={data} /> : null}
      {tab === "triage" ? (
        <TriageTab
          noticeId={params.id}
          matterId={notice.matter_id}
          onGoToDraft={() => setTab("draft")}
        />
      ) : null}
      {tab === "documents" ? <DocumentsTab data={data} /> : null}
      {tab === "draft" ? (
        <DraftTab noticeId={params.id} matterId={notice.matter_id} />
      ) : null}
      {tab === "timeline" ? <TimelineTab noticeId={params.id} /> : null}
    </main>
  );
}
