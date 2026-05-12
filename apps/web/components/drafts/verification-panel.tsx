"use client";

import { useState } from "react";

import type { DraftCitation, DraftDetail } from "@/lib/api";
import { cn } from "@/lib/cn";

interface Props {
  draft: DraftDetail;
}

type Tab = "citations" | "sourcemap";

const STATUS_TONE: Record<DraftCitation["status"], string> = {
  VERIFIED: "bg-success-bg text-success",
  VERIFIED_PARTIAL: "bg-warn-bg text-[#8B5C1F]",
  UNVERIFIED: "bg-alarm-bg text-alarm",
  STRIPPED: "bg-slate-100 text-slate",
};

const STATUS_LABEL: Record<DraftCitation["status"], string> = {
  VERIFIED: "Verified",
  VERIFIED_PARTIAL: "Partial",
  UNVERIFIED: "Unverified",
  STRIPPED: "Stripped",
};

export function VerificationPanel({ draft }: Props) {
  const [tab, setTab] = useState<Tab>("citations");
  const c = draft.citation_summary ?? {};
  const verified = (c["verified"] as number) ?? 0;
  const partial = (c["partial"] as number) ?? 0;
  const stripped = (c["stripped"] as number) ?? 0;

  return (
    <aside className="flex flex-col overflow-hidden border-l border-slate-line bg-white">
      <header className="border-b border-slate-line bg-paper px-5 py-3.5">
        <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-slate">
          Verification
        </p>
        <div className="flex flex-wrap gap-3">
          <SummaryCount label="Verified" tone="text-success" value={verified} />
          <SummaryCount label="Partial" tone="text-[#8B5C1F]" value={partial} />
          <SummaryCount label="Stripped" tone="text-alarm" value={stripped} />
        </div>
      </header>

      <div className="flex border-b border-slate-line">
        <TabBtn active={tab === "citations"} onClick={() => setTab("citations")}>
          Citations
        </TabBtn>
        <TabBtn active={tab === "sourcemap"} onClick={() => setTab("sourcemap")}>
          Source map
        </TabBtn>
      </div>

      <div className="flex-1 overflow-y-auto">
        {tab === "citations" ? <CitationsList items={draft.citations} /> : null}
        {tab === "sourcemap" ? <SourceMap items={draft.paragraph_to_source_map} /> : null}
      </div>
    </aside>
  );
}

function SummaryCount({ label, tone, value }: { label: string; tone: string; value: number }) {
  return (
    <span className="flex items-center gap-1.5 text-[12px] font-semibold text-ink">
      <span className={cn("font-serif text-[18px]", tone)}>{value}</span>
      {label}
    </span>
  );
}

function TabBtn({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex-1 border-b-2 px-4 py-2.5 text-[11px] font-semibold uppercase tracking-[0.04em] transition-colors",
        active
          ? "border-gold text-navy-deep"
          : "border-transparent text-slate hover:text-ink",
      )}
    >
      {children}
    </button>
  );
}

function CitationsList({ items }: { items: DraftCitation[] }) {
  if (items.length === 0) {
    return (
      <p className="px-5 py-8 text-center font-serif italic text-slate">
        No citations in this draft.
      </p>
    );
  }
  return (
    <ul>
      {items.map((c) => (
        <li key={c.citation_id} className="border-b border-slate-line px-5 py-3.5 last:border-b-0">
          <div className="mb-1.5 flex items-start justify-between gap-2">
            <p className="font-serif text-[13.5px] font-semibold italic text-navy-deep">
              {c.case_name}
            </p>
            <span
              className={cn(
                "shrink-0 rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide",
                STATUS_TONE[c.status],
              )}
            >
              {STATUS_LABEL[c.status]}
            </span>
          </div>
          {c.citation_string ? (
            <p className="mb-1.5 font-mono text-[10.5px] text-slate">{c.citation_string}</p>
          ) : null}
          {c.proposition_for_which_cited ? (
            <p className="mb-2 text-[12px] leading-relaxed text-ink-soft">
              {c.proposition_for_which_cited}
            </p>
          ) : null}
          <div className="flex flex-wrap items-center gap-3 text-[10.5px] text-slate">
            {c.paragraph_referenced ? <span>· {c.paragraph_referenced}</span> : null}
            {c.proposition_match_confidence != null ? (
              <span>· conf {Math.round(c.proposition_match_confidence * 100)}%</span>
            ) : null}
            {c.source_url ? (
              <a
                href={c.source_url}
                target="_blank"
                rel="noreferrer"
                className="ml-auto font-semibold uppercase tracking-[0.04em] text-gold-dark hover:text-gold"
              >
                Source ↗
              </a>
            ) : null}
          </div>
        </li>
      ))}
    </ul>
  );
}

function SourceMap({ items }: { items: Array<Record<string, unknown>> }) {
  if (items.length === 0) {
    return (
      <p className="px-5 py-8 text-center font-serif italic text-slate">
        Source map will populate after the next regeneration.
      </p>
    );
  }
  return (
    <div className="px-5 py-4">
      <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.08em] text-slate">
        Section → source
      </p>
      <dl className="space-y-2">
        {items.map((row, i) => {
          const title = (row.title as string) ?? `Section ${row.section_num}`;
          const source = row.source as { type?: string } | undefined;
          return (
            <div
              key={i}
              className="flex items-baseline justify-between gap-3 border-b border-dashed border-slate-line py-2 text-[11.5px]"
            >
              <dt className="font-semibold text-ink">{title}</dt>
              <dd className="font-serif italic text-slate">{source?.type ?? "—"}</dd>
            </div>
          );
        })}
      </dl>
    </div>
  );
}
