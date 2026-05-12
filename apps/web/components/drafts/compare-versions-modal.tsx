"use client";

import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { fetchDraft, type DraftDetail, type DraftSummary } from "@/lib/api";
import { cn } from "@/lib/cn";

interface Props {
  open: boolean;
  versions: DraftSummary[];
  currentDraftId: string;
  onClose: () => void;
}

// Side-by-side section diff. Phase 1 diff is line-based: split each section's
// body_html on <br> + paragraph boundaries and highlight added/removed lines.
// A proper structural diff lands once we move sections to a richer JSON-AST.
export function CompareVersionsModal({ open, versions, currentDraftId, onClose }: Props) {
  const sorted = useMemo(
    () => [...versions].sort((a, b) => b.version - a.version),
    [versions],
  );

  const [leftId, setLeftId] = useState<string>(sorted[1]?.draft_id ?? sorted[0]?.draft_id ?? "");
  const [rightId, setRightId] = useState<string>(currentDraftId);
  const [left, setLeft] = useState<DraftDetail | null>(null);
  const [right, setRight] = useState<DraftDetail | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open) return;
    setLeftId(sorted[1]?.draft_id ?? sorted[0]?.draft_id ?? "");
    setRightId(currentDraftId);
  }, [open, currentDraftId, sorted]);

  useEffect(() => {
    if (!open || !leftId || !rightId) return;
    let cancelled = false;
    setLoading(true);
    (async () => {
      try {
        const [l, r] = await Promise.all([fetchDraft(leftId), fetchDraft(rightId)]);
        if (cancelled) return;
        setLeft(l);
        setRight(r);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [open, leftId, rightId]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Compare draft versions"
      className="fixed inset-0 z-[1000] flex items-center justify-center bg-navy-deep/55 p-5 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative flex max-h-[92vh] w-full max-w-[1200px] flex-col overflow-hidden rounded-lg bg-paper shadow-card-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="flex items-center justify-between gap-4 border-b border-slate-line bg-white px-6 py-4">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-gold">
              Version comparison
            </p>
            <h2 className="font-serif text-[20px] font-semibold text-navy-deep">
              Side-by-side diff
            </h2>
          </div>
          <div className="flex items-center gap-3 text-[12px]">
            <label className="flex items-center gap-2">
              <span className="text-slate">Left</span>
              <select
                value={leftId}
                onChange={(e) => setLeftId(e.target.value)}
                className="rounded-sm border border-slate-line bg-white px-2.5 py-1 font-mono text-[11.5px]"
              >
                {sorted.map((v) => (
                  <option key={v.draft_id} value={v.draft_id}>
                    v{v.version}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex items-center gap-2">
              <span className="text-slate">Right</span>
              <select
                value={rightId}
                onChange={(e) => setRightId(e.target.value)}
                className="rounded-sm border border-slate-line bg-white px-2.5 py-1 font-mono text-[11.5px]"
              >
                {sorted.map((v) => (
                  <option key={v.draft_id} value={v.draft_id}>
                    v{v.version}
                  </option>
                ))}
              </select>
            </label>
            <Button variant="ghost" size="sm" onClick={onClose}>
              Close
            </Button>
          </div>
        </header>

        {loading || !left || !right ? (
          <p className="flex-1 py-12 text-center font-serif italic text-slate">Loading diff…</p>
        ) : (
          <div className="flex-1 overflow-y-auto px-6 py-5">
            <DiffView left={left} right={right} />
          </div>
        )}
      </div>
    </div>
  );
}

function DiffView({ left, right }: { left: DraftDetail; right: DraftDetail }) {
  // Pair sections by num so the alignment is stable even if reordering
  // happens in a future version (it doesn't today).
  const nums = Array.from(
    new Set([...left.sections.map((s) => s.num), ...right.sections.map((s) => s.num)]),
  ).sort((a, b) => a - b);

  return (
    <div>
      {nums.map((num) => {
        const l = left.sections.find((s) => s.num === num);
        const r = right.sections.find((s) => s.num === num);
        return (
          <section key={num} className="mb-6">
            <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.14em] text-gold-dark">
              Section {String(num).padStart(2, "0")} · {l?.title ?? r?.title}
            </p>
            <div className="grid grid-cols-2 gap-3">
              <SectionDiffPane
                lines={toLines(l?.body_html ?? "")}
                otherLines={toLines(r?.body_html ?? "")}
                mode="left"
                missingLabel={l ? null : "(added in right version)"}
              />
              <SectionDiffPane
                lines={toLines(r?.body_html ?? "")}
                otherLines={toLines(l?.body_html ?? "")}
                mode="right"
                missingLabel={r ? null : "(removed in right version)"}
              />
            </div>
          </section>
        );
      })}
    </div>
  );
}

function SectionDiffPane({
  lines,
  otherLines,
  mode,
  missingLabel,
}: {
  lines: string[];
  otherLines: string[];
  mode: "left" | "right";
  missingLabel: string | null;
}) {
  if (missingLabel) {
    return (
      <div className="rounded-sm border border-dashed border-slate-line bg-paper-tint px-3.5 py-2.5 text-[12px] italic text-slate">
        {missingLabel}
      </div>
    );
  }
  const otherSet = new Set(otherLines);
  return (
    <div className="rounded-sm border border-slate-line bg-white px-3.5 py-2.5 font-serif text-[13px] leading-relaxed">
      {lines.map((line, i) => {
        const inOther = otherSet.has(line);
        return (
          <p
            key={`${mode}-${i}`}
            className={cn(
              "mb-1.5 last:mb-0",
              !inOther && mode === "left" && "rounded-sm bg-alarm-bg/40 px-1.5 py-0.5",
              !inOther && mode === "right" && "rounded-sm bg-success-bg/60 px-1.5 py-0.5",
            )}
            dangerouslySetInnerHTML={{ __html: line }}
          />
        );
      })}
    </div>
  );
}

function toLines(html: string): string[] {
  // Split on </p> and <br> for a paragraph-line view that survives the
  // editor's contentEditable mutations.
  return html
    .replace(/<br\s*\/?>(\s*)/gi, "</p><p>")
    .split(/<\/p>\s*<p[^>]*>/i)
    .map((s) => s.replace(/^<p[^>]*>/i, "").replace(/<\/p>\s*$/i, "").trim())
    .filter((s) => s.length > 0);
}
