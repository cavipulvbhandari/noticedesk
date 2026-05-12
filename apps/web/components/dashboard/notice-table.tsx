"use client";

import { useRouter } from "next/navigation";

import type { NoticeListRow } from "@/lib/api";
import { cn } from "@/lib/cn";
import { formatDate } from "@/lib/format";

interface Props {
  notices: NoticeListRow[];
}

function daysClass(days: number): string {
  if (days < 0) return "text-alarm";
  if (days <= 3) return "text-alarm";
  if (days <= 14) return "text-gold-dark";
  return "text-slate";
}

function daysLabel(dueIso: string | null): { text: string; days: number } {
  if (!dueIso) return { text: "—", days: 9999 };
  const due = new Date(dueIso);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  due.setHours(0, 0, 0, 0);
  const diff = Math.round((due.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
  if (diff < 0) return { text: `${Math.abs(diff)} d over`, days: diff };
  if (diff === 0) return { text: "Today", days: diff };
  if (diff === 1) return { text: "Tomorrow", days: diff };
  return { text: `${diff} days`, days: diff };
}

function ingestChip(ingest: string): { label: string; tone: string } {
  if (ingest.endsWith("_portal_gsp") || ingest.endsWith("_portal_aa"))
    return { label: "⟲ portal", tone: "bg-success/10 text-success" };
  if (ingest === "email") return { label: "✉ email", tone: "bg-gold/10 text-gold-dark" };
  if (ingest === "whatsapp") return { label: "⌨ wa", tone: "bg-success/12 text-success" };
  return { label: "↑ upload", tone: "bg-paper-tint text-slate" };
}

export function NoticeTable({ notices }: Props) {
  const router = useRouter();
  if (notices.length === 0) {
    return (
      <div className="rounded-md border border-slate-line bg-white py-14 text-center">
        <p className="font-serif text-[16px] italic text-slate">
          No notices in this state — quiet for now.
        </p>
      </div>
    );
  }
  return (
    <div className="overflow-hidden rounded-md border border-slate-line bg-white">
      <table className="w-full border-collapse">
        <thead>
          <tr>
            <Th>Client</Th>
            <Th>Registration</Th>
            <Th>Type</Th>
            <Th>Issue</Th>
            <Th>FY / AY</Th>
            <Th>Due</Th>
            <Th>Days</Th>
            <Th>Assigned</Th>
            <Th>Source</Th>
          </tr>
        </thead>
        <tbody>
          {notices.map((n) => {
            const period =
              n.law === "GST"
                ? n.financial_year
                  ? `FY ${n.financial_year}`
                  : "—"
                : n.assessment_year
                  ? `AY ${n.assessment_year}`
                  : "—";
            const { text: daysText, days } = daysLabel(n.due_date);
            const ingest = ingestChip(n.ingest_channel);
            return (
              <tr
                key={n.notice_id}
                onClick={() => router.push(`/matters/${n.notice_id}`)}
                className="cursor-pointer border-b border-slate-line transition-colors last:border-b-0 hover:bg-paper"
              >
                <Td>
                  <div className="font-semibold text-ink">{n.client_legal_name}</div>
                  <div className="mt-0.5 font-mono text-[11px] text-slate">{n.client_pan}</div>
                </Td>
                <Td className="font-mono text-[11px]">
                  <div>{n.registration_identifier}</div>
                  <div className="mt-0.5 font-sans text-[10px] font-medium text-slate">
                    {n.registration_type === "GST"
                      ? (n.registration_state_name ?? n.registration_state_code ?? "GST")
                      : "Income Tax"}
                  </div>
                </Td>
                <Td>
                  <span
                    className={cn(
                      "whitespace-nowrap rounded-full px-2.5 py-0.5 text-[10.5px] font-semibold uppercase tracking-wide",
                      n.law === "GST"
                        ? "bg-gold/15 text-gold-dark"
                        : "bg-navy/10 text-navy",
                    )}
                  >
                    {n.document_type ?? n.law}
                  </span>
                </Td>
                <Td>{n.issue ?? "—"}</Td>
                <Td>{period}</Td>
                <Td className="font-medium text-ink">
                  {n.due_date ? formatDate(n.due_date) : "—"}
                </Td>
                <Td className={cn("font-mono text-[11.5px] font-semibold", daysClass(days))}>
                  {daysText}
                </Td>
                <Td>{n.assigned_to ?? "—"}</Td>
                <Td>
                  <span
                    className={cn(
                      "rounded-full px-2.5 py-0.5 text-[10.5px] font-semibold",
                      ingest.tone,
                    )}
                  >
                    {ingest.label}
                  </span>
                </Td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return (
    <th className="whitespace-nowrap border-b border-slate-line bg-paper px-4 py-3 text-left text-[10.5px] font-semibold uppercase tracking-[0.06em] text-slate">
      {children}
    </th>
  );
}

function Td({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <td className={`px-4 py-3.5 align-middle text-[13px] text-ink-soft ${className}`}>
      {children}
    </td>
  );
}
