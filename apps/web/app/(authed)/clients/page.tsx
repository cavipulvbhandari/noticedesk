"use client";

import { FileSpreadsheet, Plus } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { AddClientModal } from "@/components/clients/add-client-modal";
import { ClientsTable } from "@/components/clients/clients-table";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast";
import { fetchClients, type ClientList } from "@/lib/api";

export default function ClientsPage() {
  const [data, setData] = useState<ClientList | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [addOpen, setAddOpen] = useState(false);
  const { toast } = useToast();

  const load = useCallback(async () => {
    try {
      const next = await fetchClients();
      setData(next);
      setError(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "failed to load clients");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const clients = data?.clients ?? [];
  const total = data?.total ?? 0;
  const gstRegTotal = clients.reduce((sum, c) => sum + c.gst_count, 0);
  // Every client has exactly one IT registration (auto-created on creation).
  const itRegTotal = total;

  return (
    <main className="mx-auto max-w-[1400px] px-10 py-8 pb-16">
      <header className="mb-8 flex flex-wrap items-end justify-between gap-6">
        <div>
          <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.08em] text-ink">
            Clients
          </p>
          <h1 className="font-serif text-[36px] font-medium leading-tight tracking-tight text-navy-deep">
            Clients
          </h1>
          <p className="mt-1 font-serif text-[17px] italic text-slate">
            {total} {total === 1 ? "client" : "clients"} · {gstRegTotal} GST{" "}
            {gstRegTotal === 1 ? "registration" : "registrations"} · {itRegTotal} IT{" "}
            {itRegTotal === 1 ? "registration" : "registrations"}
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <Button
            variant="ghost"
            size="sm"
            className="border border-slate-line bg-white hover:bg-paper"
            onClick={() => toast("Excel migration arrives in Phase 2", "info")}
          >
            <FileSpreadsheet className="mr-1.5 h-3.5 w-3.5" aria-hidden />
            Import from Excel
          </Button>
          <Button variant="gold" size="sm" onClick={() => setAddOpen(true)}>
            <Plus className="mr-1.5 h-3.5 w-3.5" aria-hidden />
            Add client
          </Button>
        </div>
      </header>

      {error ? (
        <p className="mb-4 rounded border border-alarm/30 bg-alarm-bg px-3 py-2 text-sm text-alarm">
          {error}
        </p>
      ) : null}

      {loading && clients.length === 0 ? (
        <p className="py-12 text-center font-serif italic text-slate">Loading clients…</p>
      ) : clients.length === 0 ? (
        <div className="rounded-md border border-dashed border-slate-line bg-white p-12 text-center">
          <p className="font-serif text-lg text-navy-deep">No clients yet</p>
          <p className="mt-1 text-sm text-slate">
            Add your first client to start routing notices.
          </p>
        </div>
      ) : (
        <ClientsTable clients={clients} />
      )}

      <AddClientModal
        open={addOpen}
        onClose={() => setAddOpen(false)}
        onCreated={(clientId) => {
          toast("Client added · IT registration created automatically", "success");
          setAddOpen(false);
          void load();
          // Silence unused-var lint for now; future slice will navigate to the
          // newly created client's detail page using this id.
          void clientId;
        }}
      />
    </main>
  );
}
