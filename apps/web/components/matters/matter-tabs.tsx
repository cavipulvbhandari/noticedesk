"use client";

import { cn } from "@/lib/cn";

export type MatterTab =
  | "notice"
  | "triage"
  | "documents"
  | "draft"
  | "timeline";

const TABS: { key: MatterTab; label: string }[] = [
  { key: "notice", label: "Notice" },
  { key: "triage", label: "Triage" },
  { key: "documents", label: "Documents" },
  { key: "draft", label: "Draft reply" },
  { key: "timeline", label: "Timeline" },
];

interface Props {
  active: MatterTab;
  onChange: (key: MatterTab) => void;
  counts?: Partial<Record<MatterTab, number>>;
}

export function MatterTabs({ active, onChange, counts }: Props) {
  return (
    <div className="mb-5 flex gap-1 border-b border-slate-line">
      {TABS.map((t) => {
        const isActive = active === t.key;
        const count = counts?.[t.key];
        return (
          <button
            key={t.key}
            type="button"
            onClick={() => onChange(t.key)}
            className={cn(
              "-mb-px border-b-2 px-4 py-2.5 text-[13px] font-semibold transition-colors",
              isActive
                ? "border-gold text-navy-deep"
                : "border-transparent text-slate hover:text-ink",
            )}
          >
            {t.label}
            {typeof count === "number" ? (
              <span className="ml-1.5 rounded-full bg-paper-tint px-1.5 py-0.5 text-[10.5px] font-bold text-slate">
                {count}
              </span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
