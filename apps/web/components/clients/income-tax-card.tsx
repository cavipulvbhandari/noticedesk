"use client";

import { Button } from "@/components/ui/button";
import type { ClientRegistration } from "@/lib/api";
import { formatDate } from "@/lib/format";

interface Props {
  itReg: ClientRegistration | null;
  onViewAll: () => void;
}

export function IncomeTaxCard({ itReg, onViewAll }: Props) {
  return (
    <article className="flex flex-col overflow-hidden rounded-md border border-slate-line bg-white">
      <header className="bg-navy px-6 py-4.5 text-paper">
        <p className="text-[10.5px] font-bold uppercase tracking-[0.14em] text-paper/85">
          Income Tax
        </p>
        <h2 className="mt-1 font-serif text-[22px] font-semibold tracking-tight">
          Income Tax
        </h2>
        <p className="mt-0.5 font-mono text-[12px] tracking-wide opacity-85">
          {itReg?.identifier_value ?? "—"}
        </p>
      </header>

      <div className="flex flex-1 flex-col px-6 py-5">
        <div className="mb-4 flex items-baseline justify-between">
          <div>
            <p className="font-serif text-[28px] font-semibold leading-none tracking-tight text-navy-deep">
              {itReg?.active_notice_count ?? 0}
            </p>
            <p className="mt-1.5 text-[12px] font-medium text-slate">active notices</p>
          </div>
        </div>

        {itReg?.earliest_open_due_date ? (
          <div className="mb-5 flex items-center justify-between">
            <span className="text-[11px] font-semibold uppercase tracking-[0.05em] text-slate">
              Earliest deadline
            </span>
            <span className="font-serif text-[16px] font-semibold italic text-alarm">
              {formatDate(itReg.earliest_open_due_date)}
            </span>
          </div>
        ) : (
          <p className="mb-5 font-serif text-[13px] italic text-slate">
            No open deadlines
          </p>
        )}

        <div className="mt-auto flex items-center justify-between border-t border-slate-line pt-4">
          <span className="flex items-center gap-1.5 text-[10.5px] font-medium text-slate">
            <span className="h-1.5 w-1.5 rounded-full bg-slate-pale" />
            Manual entry · Portal sync coming soon
          </span>
          <Button variant="ghost" size="sm" onClick={onViewAll}>
            View all notices →
          </Button>
        </div>
      </div>
    </article>
  );
}
