"use client";

import { cn } from "@/lib/cn";
import type { Lifecycle } from "@/lib/lifecycle";

interface TabDef {
  key: Lifecycle;
  label: string;
  alarm?: boolean;
}

// Same eight statuses as the prototype — order is significant (left-to-right
// matches the partner's mental "notice age" walk).
const TABS: TabDef[] = [
  { key: "issued", label: "Issued" },
  { key: "in_progress", label: "In Progress" },
  { key: "due", label: "Due" },
  { key: "due_date_over", label: "Due Date Over", alarm: true },
  { key: "reply_submitted", label: "Reply Submitted" },
  { key: "acknowledged", label: "Acknowledged" },
  { key: "order_received", label: "Order Received" },
  { key: "appeal_filed", label: "Appeal Filed" },
];

interface Props {
  counts: Record<string, number>;
  active: string;
  onChange: (key: Lifecycle) => void;
}

export function StatusTabs({ counts, active, onChange }: Props) {
  return (
    <div className="mb-7 grid grid-cols-2 gap-px overflow-hidden rounded-md border border-slate-line bg-slate-line lg:grid-cols-8">
      {TABS.map((t) => {
        const isActive = active === t.key;
        const value = counts[t.key] ?? 0;
        return (
          <button
            key={t.key}
            type="button"
            onClick={() => onChange(t.key)}
            className={cn(
              "px-3 py-3.5 text-left transition-colors",
              isActive
                ? t.alarm
                  ? "bg-alarm text-paper"
                  : "bg-navy text-paper"
                : "bg-white hover:bg-paper",
            )}
          >
            <p
              className={cn(
                "mb-1.5 text-[10px] font-semibold uppercase leading-tight tracking-[0.08em]",
                isActive ? "text-paper/75" : "text-slate",
              )}
            >
              {t.label}
            </p>
            <p
              className={cn(
                "font-serif text-[24px] font-semibold leading-none",
                isActive
                  ? "text-paper"
                  : t.alarm
                    ? "text-alarm"
                    : "text-navy-deep",
              )}
            >
              {value}
            </p>
          </button>
        );
      })}
    </div>
  );
}
