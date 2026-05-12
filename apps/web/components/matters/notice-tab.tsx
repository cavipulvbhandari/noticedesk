"use client";

import { useState } from "react";

import type { NoticeDetail } from "@/lib/api";

interface Props {
  data: NoticeDetail;
}

interface DocItem {
  text: string;
  checked: boolean;
}

// "Notice" tab: AI-generated notice understanding (issue text from the
// parsed JSON when available), parsed fields panel, and the documents-
// required checklist. The checklist is local-only for Phase 1 — wiring it
// to a persisted "evidence collected" model arrives with the file-upload
// slice in Sprint 5.
export function NoticeTab({ data }: Props) {
  const { notice } = data;
  const docs = extractDocsRequired(notice);
  const [checks, setChecks] = useState<DocItem[]>(
    docs.map((d) => ({ text: d, checked: false })),
  );

  const parsedFields: Array<[string, string | null]> = [
    ["Document type", notice.document_type],
    ["Notice number", notice.notice_number],
    ["DIN / RFN", notice.din_or_rfn],
    ["Issue date", notice.issue_date],
    ["Receipt date", notice.receipt_date],
    ["Due date", notice.due_date],
    ["Hearing date", notice.hearing_date],
    ["Authority", notice.authority],
    ["Financial year", notice.financial_year],
    ["Assessment year", notice.assessment_year],
    ["Demand amount", notice.demand_amount ? `₹${notice.demand_amount}` : null],
    [
      "Parse confidence",
      typeof notice.parse_confidence === "number"
        ? `${(notice.parse_confidence * 100).toFixed(0)}%`
        : null,
    ],
  ];

  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-[2fr_1fr]">
      <article className="rounded-md border border-slate-line bg-paper px-6 py-5">
        <p className="mb-2.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-gold-dark">
          Notice understanding
        </p>
        {notice.issue ? (
          <p className="font-serif text-[15px] italic leading-relaxed text-ink">
            {notice.issue}
          </p>
        ) : (
          <p className="font-serif text-[14px] italic text-slate">
            No structured summary yet — the document parser ran with the stub
            provider for this notice. Upload the source PDF from the inbox to
            regenerate the parsed view.
          </p>
        )}
        {notice.assigned_to ? (
          <p className="mt-4 border-t border-slate-line pt-3 text-[11.5px] text-slate">
            Assigned to{" "}
            <strong className="font-semibold text-gold-dark">{notice.assigned_to}</strong>
          </p>
        ) : null}
      </article>

      <article className="overflow-hidden rounded-md border border-slate-line bg-white">
        <header className="border-b border-slate-line bg-paper px-5 py-3 text-[11px] font-semibold uppercase tracking-[0.08em] text-slate">
          Parsed fields
        </header>
        <dl className="px-5 py-2">
          {parsedFields
            .filter(([, v]) => v != null && v !== "")
            .map(([label, value]) => (
              <div
                key={label}
                className="flex items-baseline justify-between gap-3 border-b border-dashed border-slate-line py-2 last:border-b-0"
              >
                <dt className="text-[11.5px] text-slate">{label}</dt>
                <dd className="text-right text-[12.5px] font-medium text-ink">{value}</dd>
              </div>
            ))}
        </dl>
      </article>

      <article className="overflow-hidden rounded-md border border-slate-line bg-white lg:col-span-2">
        <header className="flex items-center justify-between border-b border-slate-line bg-paper px-5 py-3">
          <h3 className="font-serif text-[15px] font-semibold text-navy-deep">
            Documents required
          </h3>
          <span className="text-[11.5px] font-medium text-slate">
            {checks.filter((c) => c.checked).length} / {checks.length} ready
          </span>
        </header>
        {checks.length === 0 ? (
          <p className="px-5 py-8 text-center font-serif italic text-slate">
            No document checklist was extracted for this notice.
          </p>
        ) : (
          <ul>
            {checks.map((c, i) => (
              <li
                key={i}
                onClick={() =>
                  setChecks((prev) =>
                    prev.map((p, j) => (j === i ? { ...p, checked: !p.checked } : p)),
                  )
                }
                className="flex cursor-pointer items-start gap-3 border-b border-slate-line px-5 py-3 transition-colors last:border-b-0 hover:bg-paper"
              >
                <span
                  className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-sm border ${
                    c.checked
                      ? "border-success bg-success text-white"
                      : "border-slate-pale bg-white"
                  }`}
                >
                  {c.checked ? "✓" : ""}
                </span>
                <span
                  className={`text-[13px] ${c.checked ? "text-slate line-through" : "text-ink"}`}
                >
                  {c.text}
                </span>
              </li>
            ))}
          </ul>
        )}
      </article>
    </div>
  );
}

function extractDocsRequired(notice: NoticeDetail["notice"]): string[] {
  // Two storage locations: notice.documents_required JSONB (when the parser
  // explicitly extracted them) or notice.raw_extracted_json.documents_required
  // (when the parser stuffed everything in raw). Try both.
  const fromColumn = notice.documents_required;
  if (Array.isArray(fromColumn)) return fromColumn.filter((s): s is string => typeof s === "string");
  const raw = notice.raw_extracted_json;
  if (raw && Array.isArray((raw as { documents_required?: unknown }).documents_required)) {
    return ((raw as { documents_required: unknown[] }).documents_required).filter(
      (s): s is string => typeof s === "string",
    );
  }
  return [];
}
