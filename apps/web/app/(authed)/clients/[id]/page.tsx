"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { AddGstModal } from "@/components/clients/add-gst-modal";
import { ClientDetailHeader } from "@/components/clients/client-detail-header";
import { EditClientModal } from "@/components/clients/edit-client-modal";
import { GstCard } from "@/components/clients/gst-card";
import { IncomeTaxCard } from "@/components/clients/income-tax-card";
import { InfoModal } from "@/components/ui/info-modal";
import { useToast } from "@/components/ui/toast";
import { fetchClient, type ClientDetail } from "@/lib/api";

interface Props {
  params: { id: string };
}

export default function ClientDetailPage({ params }: Props) {
  const router = useRouter();
  const { toast } = useToast();
  const [data, setData] = useState<ClientDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [addGstOpen, setAddGstOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [syncInfo, setSyncInfo] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const next = await fetchClient(params.id);
      setData(next);
      setError(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "failed to load client");
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
        <p className="py-12 text-center font-serif italic text-slate">Loading client…</p>
      </main>
    );
  }

  if (error || !data) {
    return (
      <main className="mx-auto max-w-[1400px] px-10 py-8">
        <p className="rounded border border-alarm/30 bg-alarm-bg px-3 py-2 text-sm text-alarm">
          {error ?? "Client not found"}
        </p>
      </main>
    );
  }

  const itReg = data.registrations.find((r) => r.registration_type === "IT") ?? null;
  const gstRegs = data.registrations.filter((r) => r.registration_type === "GST");

  return (
    <main className="mx-auto max-w-[1400px] px-10 py-8 pb-16">
      <nav className="mb-3.5 flex items-center gap-2 text-[11px] font-medium uppercase tracking-[0.08em] text-slate">
        <a
          className="cursor-pointer hover:text-ink"
          onClick={() => router.push("/clients")}
        >
          Clients
        </a>
        <span className="text-slate-pale">›</span>
        <span className="font-semibold text-ink">{data.legal_name}</span>
      </nav>

      <ClientDetailHeader
        client={data}
        onEdit={() => setEditOpen(true)}
        onDeleted={() => {
          toast("Client deleted", "success");
          router.push("/clients");
        }}
      />

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <IncomeTaxCard
          itReg={itReg}
          onViewAll={() => router.push(`/clients/${data.client_id}/it`)}
        />
        <GstCard
          clientId={data.client_id}
          gstRegs={gstRegs}
          onSelectReg={(regId) =>
            router.push(`/clients/${data.client_id}/gst/${regId}`)
          }
          onAddGst={() => setAddGstOpen(true)}
          onSyncStub={(label) => setSyncInfo(label)}
        />
      </div>

      <AddGstModal
        open={addGstOpen}
        clientId={data.client_id}
        clientLegalName={data.legal_name}
        clientPan={data.pan}
        onClose={() => setAddGstOpen(false)}
        onCreated={() => {
          toast("GST registration added", "success");
          setAddGstOpen(false);
          void load();
        }}
      />

      <EditClientModal
        open={editOpen}
        client={data}
        onClose={() => setEditOpen(false)}
        onSaved={() => {
          toast("Client updated", "success");
          setEditOpen(false);
          void load();
        }}
      />

      <InfoModal
        open={syncInfo !== null}
        title="Portal sync arrives in Phase 2"
        eyebrow="Coming soon"
        onClose={() => setSyncInfo(null)}
      >
        <p className="mb-3">
          We&rsquo;ll connect {syncInfo ?? "this registration"} directly to the GST
          GSP / Income Tax AA portal so notices arrive without manual upload and
          replies are filed straight from NoticeDesk.
        </p>
        <p className="text-slate">
          For Phase 1, drop scanned PDFs into the inbox or forward emails to your
          firm&rsquo;s ingestion address &mdash; routing happens automatically.
        </p>
      </InfoModal>
    </main>
  );
}
