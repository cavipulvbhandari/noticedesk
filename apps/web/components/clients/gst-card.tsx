"use client";

import { Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { ClientRegistration } from "@/lib/api";
import { formatDate } from "@/lib/format";

interface Props {
  clientId: string;
  gstRegs: ClientRegistration[];
  onSelectReg: (registrationId: string) => void;
  onAddGst: () => void;
  onSyncStub: (gstinLabel: string) => void;
}

export function GstCard({ clientId, gstRegs, onSelectReg, onAddGst, onSyncStub }: Props) {
  const totalActive = gstRegs.reduce((sum, r) => sum + r.active_notice_count, 0);
  void clientId; // for future routing variants
  return (
    <article className="flex flex-col overflow-hidden rounded-md border border-slate-line bg-white">
      <header className="bg-gold px-6 py-4.5 text-paper">
        <p className="text-[10.5px] font-bold uppercase tracking-[0.14em] text-paper/85">
          Goods &amp; Services Tax
        </p>
        <h2 className="mt-1 font-serif text-[22px] font-semibold tracking-tight">GST</h2>
        <p className="mt-0.5 text-[12px] opacity-85">
          {gstRegs.length} state {gstRegs.length === 1 ? "registration" : "registrations"} ·{" "}
          {totalActive} active {totalActive === 1 ? "notice" : "notices"}
        </p>
      </header>

      <div className="flex flex-1 flex-col px-6 py-5">
        {gstRegs.length > 0 ? (
          <ul className="mb-5 flex flex-col gap-2">
            {gstRegs.map((r) => (
              <li
                key={r.registration_id}
                className="group cursor-pointer rounded-sm border border-slate-line bg-paper px-4 py-3.5 transition-colors hover:border-gold hover:bg-white"
                onClick={() => onSelectReg(r.registration_id)}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="font-serif text-[14px] font-semibold text-navy-deep">
                      {r.state_name ?? r.state_code ?? "—"}
                    </p>
                    <p className="mt-0.5 font-mono text-[11.5px] font-semibold text-ink">
                      {r.identifier_value}
                    </p>
                    <p className="mt-0.5 text-[11px] text-slate">
                      State code {r.state_code ?? "—"} · {r.registration_status ?? "active"}
                    </p>
                  </div>
                  <div className="shrink-0 text-right">
                    <p className="font-serif text-[18px] font-semibold leading-none text-navy-deep">
                      {r.active_notice_count}
                    </p>
                    <p className="mt-0.5 text-[10px] uppercase tracking-wide text-slate">
                      active
                    </p>
                    {r.earliest_open_due_date ? (
                      <p className="mt-1.5 font-serif text-[11px] font-semibold italic text-alarm">
                        {formatDate(r.earliest_open_due_date)}
                      </p>
                    ) : null}
                  </div>
                </div>
                <div className="mt-2.5 flex items-center justify-between border-t border-dashed border-slate-line pt-2.5 text-[10.5px] text-slate">
                  <span className="flex items-center gap-1.5">
                    <span
                      className={`h-1.5 w-1.5 rounded-full ${
                        r.sync_method === "portal" ? "bg-success" : "bg-slate-pale"
                      }`}
                    />
                    {r.sync_method === "portal" ? "Portal · connected" : "Manual entry only"}
                  </span>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onSyncStub(r.identifier_value);
                    }}
                    className="text-[10.5px] font-semibold uppercase tracking-[0.04em] text-gold-dark hover:text-gold"
                  >
                    {r.sync_method === "portal" ? "Sync now" : "Connect portal"}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <div className="mb-5 rounded-sm border border-dashed border-slate-line bg-paper px-4 py-6 text-center">
            <p className="font-serif text-[14px] font-semibold text-navy-deep">
              No GST registrations yet
            </p>
            <p className="mt-1 text-[12px] text-slate">
              Add a GSTIN to start tracking GST notices for this client.
            </p>
          </div>
        )}

        <div className="mt-auto flex items-center justify-end border-t border-slate-line pt-4">
          <Button variant="ghost" size="sm" onClick={onAddGst}>
            <Plus className="mr-1.5 h-3.5 w-3.5" aria-hidden />
            Add GST registration
          </Button>
        </div>
      </div>
    </article>
  );
}
