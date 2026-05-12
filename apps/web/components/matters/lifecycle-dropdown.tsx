"use client";

import { useEffect, useRef, useState } from "react";

import { cn } from "@/lib/cn";
import { LIFECYCLE_LABELS, lifecycleChipClass, type Lifecycle } from "@/lib/lifecycle";

const REASON_REQUIRED: ReadonlySet<string> = new Set([
  "closed",
  "on_hold",
  "reply_submitted",
]);

const TARGETS: Lifecycle[] = [
  "issued",
  "in_progress",
  "due",
  "due_date_over",
  "reply_submitted",
  "acknowledged",
  "order_received",
  "appeal_filed",
  "closed",
  "on_hold",
];

interface Props {
  current: string;
  disabled?: boolean;
  onTransition: (next: string, reason: string | null) => Promise<void>;
}

// Clickable chip → popover dropdown of valid next states. Phase 1 doesn't
// constrain transitions (the brief explicitly says partners move notices
// manually with no state-machine), so we list every state and let the user
// pick. Transitions to closed / on_hold / reply_submitted require a reason —
// the popover shows the reason textarea inline and disables the Confirm
// button until the reason has content.
export function LifecycleDropdown({ current, disabled, onTransition }: Props) {
  const [open, setOpen] = useState(false);
  const [picked, setPicked] = useState<string | null>(null);
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
        setPicked(null);
        setReason("");
        setError(null);
      }
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  async function handleConfirm() {
    if (!picked) return;
    if (REASON_REQUIRED.has(picked) && !reason.trim()) {
      setError("Please add a reason for this transition.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await onTransition(picked, reason.trim() || null);
      setOpen(false);
      setPicked(null);
      setReason("");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "transition failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div ref={ref} className="relative inline-block">
      <button
        type="button"
        disabled={disabled}
        onClick={() => setOpen((o) => !o)}
        className={cn(
          "inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-wide transition-shadow",
          lifecycleChipClass(current),
          !disabled && "cursor-pointer hover:shadow-card-sm",
          disabled && "cursor-not-allowed opacity-60",
        )}
        title="Change lifecycle"
      >
        {LIFECYCLE_LABELS[current as Lifecycle] ?? current}
        <svg className="h-2.5 w-2.5 opacity-70" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {open ? (
        <div className="absolute right-0 top-full z-40 mt-2 w-[300px] rounded-md border border-slate-line bg-white p-3 shadow-card-lg">
          <p className="mb-2 text-[10.5px] font-semibold uppercase tracking-[0.06em] text-slate">
            Move to
          </p>
          <ul className="mb-2 max-h-[200px] space-y-1 overflow-y-auto">
            {TARGETS.filter((t) => t !== current).map((t) => (
              <li key={t}>
                <button
                  type="button"
                  onClick={() => {
                    setPicked(t);
                    setError(null);
                  }}
                  className={cn(
                    "w-full rounded-sm px-2.5 py-1.5 text-left text-[13px] transition-colors",
                    picked === t
                      ? "bg-navy text-paper"
                      : "text-ink hover:bg-paper",
                  )}
                >
                  {LIFECYCLE_LABELS[t]}
                  {REASON_REQUIRED.has(t) ? (
                    <span className="ml-1.5 text-[10px] uppercase tracking-wide text-slate-soft">
                      reason required
                    </span>
                  ) : null}
                </button>
              </li>
            ))}
          </ul>

          {picked ? (
            <>
              <label className="mb-1 block text-[10.5px] font-semibold uppercase tracking-[0.06em] text-slate">
                Reason {REASON_REQUIRED.has(picked) ? <span className="text-alarm">*</span> : null}
              </label>
              <textarea
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                rows={2}
                placeholder={
                  REASON_REQUIRED.has(picked)
                    ? "e.g. Reply filed with department on 2026-05-10"
                    : "Optional note for the timeline"
                }
                className="mb-2 w-full rounded-sm border border-slate-line bg-white px-2.5 py-1.5 text-[12px] outline-none focus:border-gold"
              />
              {error ? (
                <p className="mb-2 text-[11px] text-alarm">{error}</p>
              ) : null}
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setPicked(null);
                    setReason("");
                    setError(null);
                  }}
                  className="rounded-sm px-3 py-1 text-[12px] font-medium text-slate hover:bg-paper"
                  disabled={busy}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleConfirm}
                  disabled={busy}
                  className="rounded-sm bg-navy px-3 py-1 text-[12px] font-semibold text-paper hover:bg-navy-deep disabled:opacity-60"
                >
                  {busy ? "Saving…" : "Confirm"}
                </button>
              </div>
            </>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
