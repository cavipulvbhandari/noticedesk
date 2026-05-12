"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { deleteClient, type ClientDetail } from "@/lib/api";
import { useToast } from "@/components/ui/toast";

interface Props {
  client: ClientDetail;
  onEdit: () => void;
  onDeleted: () => void;
}

export function ClientDetailHeader({ client, onEdit, onDeleted }: Props) {
  const { toast } = useToast();
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);

  async function handleDelete() {
    setDeleting(true);
    try {
      await deleteClient(client.client_id);
      onDeleted();
    } catch (e: unknown) {
      toast(e instanceof Error ? e.message : "delete failed", "error");
      setDeleting(false);
      setConfirming(false);
    }
  }

  return (
    <header className="relative mb-6 overflow-hidden rounded-md border border-slate-line bg-white px-8 py-7">
      <div className="absolute inset-x-0 top-0 h-[3px] bg-gradient-to-r from-gold to-gold-dark" />
      <div className="flex items-start justify-between gap-6">
        <div className="min-w-0">
          <p className="mb-2.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-gold">
            Client detail view
          </p>
          <h1 className="mb-3 font-serif text-[32px] font-semibold tracking-tight text-navy-deep">
            {client.legal_name}
          </h1>
          <dl className="flex flex-wrap gap-x-7 gap-y-2 text-[12.5px] text-slate">
            <Meta label="PAN" value={client.pan} mono />
            <Meta label="Entity" value={client.entity_type ?? "—"} />
            <Meta label="Industry" value={client.industry ?? "—"} />
            {client.trade_name ? <Meta label="Trade name" value={client.trade_name} /> : null}
          </dl>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Button variant="ghost" size="sm" onClick={onEdit}>
            Edit
          </Button>
          {confirming ? (
            <div className="flex items-center gap-2 rounded-sm border border-alarm/30 bg-alarm-bg px-2.5 py-1.5">
              <span className="text-xs text-alarm">Delete this client?</span>
              <Button
                variant="ghost"
                size="sm"
                className="text-xs"
                onClick={() => setConfirming(false)}
                disabled={deleting}
              >
                Cancel
              </Button>
              <button
                type="button"
                onClick={handleDelete}
                disabled={deleting}
                className="rounded-sm bg-alarm px-2.5 py-1 text-xs font-semibold text-white hover:bg-alarm/90 disabled:opacity-50"
              >
                {deleting ? "Deleting…" : "Delete"}
              </button>
            </div>
          ) : (
            <Button
              variant="ghost"
              size="sm"
              className="text-alarm hover:bg-alarm-bg"
              onClick={() => setConfirming(true)}
            >
              Delete
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}

function Meta({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-center gap-1.5">
      <dt className="text-[11px] font-semibold uppercase tracking-[0.04em] text-slate-soft">
        {label}
      </dt>
      <dd className={`font-medium text-ink ${mono ? "font-mono text-[12px]" : ""}`}>
        {value}
      </dd>
    </div>
  );
}
