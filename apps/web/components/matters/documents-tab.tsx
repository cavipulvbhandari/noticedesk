"use client";

// The full implementation arrives with the file-upload features in Sprint 5
// (per the brief). For Phase 1 we render a single row referencing the source
// inbox upload if there is one, and otherwise an empty state.

import type { NoticeDetail } from "@/lib/api";

export function DocumentsTab({ data }: { data: NoticeDetail }) {
  const sourceInbox = data.notice.source_inbox_id;
  return (
    <div className="overflow-hidden rounded-md border border-slate-line bg-white">
      <header className="border-b border-slate-line bg-paper px-5 py-3">
        <h3 className="font-serif text-[15px] font-semibold text-navy-deep">Documents</h3>
      </header>
      {sourceInbox ? (
        <table className="w-full border-collapse">
          <thead>
            <tr>
              <Th>Type</Th>
              <Th>Source</Th>
              <Th>Reference</Th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b border-slate-line last:border-b-0">
              <Td>Original notice</Td>
              <Td>Inbox upload</Td>
              <Td className="font-mono text-[11.5px]">{sourceInbox}</Td>
            </tr>
          </tbody>
        </table>
      ) : (
        <div className="px-5 py-10 text-center">
          <p className="font-serif text-[15px] italic text-slate">
            No source document attached.
          </p>
          <p className="mt-1 text-[12px] text-slate">
            File attachments (reply drafts, supporting evidence, working
            papers) arrive in Sprint 5.
          </p>
        </div>
      )}
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return (
    <th className="border-b border-slate-line bg-paper px-4 py-3 text-left text-[10.5px] font-semibold uppercase tracking-[0.06em] text-slate">
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
    <td className={`px-4 py-3 align-middle text-[13px] text-ink-soft ${className}`}>{children}</td>
  );
}
