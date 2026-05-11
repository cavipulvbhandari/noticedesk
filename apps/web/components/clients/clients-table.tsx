"use client";

import type { ClientSummary } from "@/lib/api";
import { formatDate } from "@/lib/format";

interface Props {
  clients: ClientSummary[];
}

export function ClientsTable({ clients }: Props) {
  return (
    <div className="overflow-hidden rounded-md border border-slate-line bg-white">
      <table className="w-full border-collapse">
        <thead>
          <tr>
            <Th>Legal name</Th>
            <Th>PAN</Th>
            <Th>Entity</Th>
            <Th>GST regs</Th>
            <Th>Active IT</Th>
            <Th>Active GST</Th>
            <Th>Earliest deadline</Th>
          </tr>
        </thead>
        <tbody>
          {clients.map((c) => (
            <tr
              key={c.client_id}
              className="cursor-pointer border-b border-slate-line transition-colors last:border-b-0 hover:bg-paper"
            >
              <Td>
                <div className="font-semibold text-ink">{c.legal_name}</div>
                {c.industry ? (
                  <div className="mt-0.5 text-[11px] text-slate">{c.industry}</div>
                ) : null}
              </Td>
              <Td className="font-mono text-[11px] text-slate">{c.pan}</Td>
              <Td>{c.entity_type ?? "—"}</Td>
              <Td>
                {c.gst_count}
                {c.gst_count > 0 ? (
                  <span className="ml-1 text-[10px] text-slate">
                    ({c.gst_state_codes.join(", ")})
                  </span>
                ) : null}
              </Td>
              <Td>
                <strong className="font-serif text-[15px] font-semibold text-ink">
                  {c.active_it_count}
                </strong>
              </Td>
              <Td>
                <strong className="font-serif text-[15px] font-semibold text-ink">
                  {c.active_gst_count}
                </strong>
              </Td>
              <Td>
                {c.earliest_open_due_date ? (
                  <span className="font-serif font-semibold italic text-alarm">
                    {formatDate(c.earliest_open_due_date)}
                  </span>
                ) : (
                  <span className="text-slate">—</span>
                )}
              </Td>
            </tr>
          ))}
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
