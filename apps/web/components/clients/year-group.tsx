"use client";

import { useRouter } from "next/navigation";

import type { RegistrationNotice } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { lifecycleChipClass, lifecycleLabel } from "@/lib/lifecycle";

interface Props {
  title: string;
  notices: RegistrationNotice[];
}

// Year-grouped notice list used by both the IT drilldown (groups by AY) and
// the GST drilldown (groups by FY). Sorts inside the group by due_date ASC
// so the most pressing notice for that year is on top.
export function YearGroup({ title, notices }: Props) {
  const router = useRouter();
  const sorted = [...notices].sort((a, b) => {
    const ad = a.due_date ? Date.parse(a.due_date) : Infinity;
    const bd = b.due_date ? Date.parse(b.due_date) : Infinity;
    return ad - bd;
  });
  return (
    <section className="mb-4 overflow-hidden rounded-md border border-slate-line bg-white">
      <header className="flex items-center justify-between border-b border-slate-line bg-paper px-5 py-3.5">
        <h3 className="font-serif text-[16px] font-semibold text-navy-deep">{title}</h3>
        <span className="text-[11px] font-medium tracking-wide text-slate">
          {notices.length} {notices.length === 1 ? "notice" : "notices"}
        </span>
      </header>
      <ul>
        {sorted.map((n) => (
          <li
            key={n.notice_id}
            onClick={() => router.push(`/matters/${n.notice_id}`)}
            className="grid cursor-pointer grid-cols-[auto_1fr_auto_auto_auto] items-center gap-4 border-b border-slate-line px-5 py-3.5 transition-colors last:border-b-0 hover:bg-paper"
          >
            <span className="whitespace-nowrap rounded-sm bg-gold/10 px-2.5 py-1 font-mono text-[11px] font-semibold text-gold-dark">
              {n.document_type ?? "—"}
            </span>
            <div className="min-w-0">
              <p className="truncate text-[13px] text-ink">{n.issue ?? "—"}</p>
              {n.authority ? (
                <p className="mt-0.5 truncate text-[11px] text-slate">{n.authority}</p>
              ) : null}
            </div>
            <div className="text-right">
              <p className="text-[10px] font-semibold uppercase tracking-wide text-slate">
                Due
              </p>
              <p className="whitespace-nowrap font-serif text-[13px] font-medium text-ink">
                {n.due_date ? formatDate(n.due_date) : "—"}
              </p>
            </div>
            <span
              className={`whitespace-nowrap rounded-full px-2.5 py-0.5 text-[10.5px] font-semibold uppercase tracking-wide ${lifecycleChipClass(n.lifecycle_status)}`}
            >
              {lifecycleLabel(n.lifecycle_status)}
            </span>
            <span className="whitespace-nowrap text-[11.5px] text-slate">
              {n.assigned_to ?? "—"}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
