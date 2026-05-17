"use client";

import { useEffect, useState } from "react";

import { cn } from "@/lib/cn";

// Five named steps the user sees during the ~60-90s wait. Real progress
// events would come from a Temporal-fronted progress endpoint; this is
// purely visual pacing for the Phase 1 inline workflow.
const STEPS = [
  { at: 0,  label: "Loading registration-scoped context…" },
  { at: 8,  label: "Drafting 15-section reply via Claude Opus…" },
  { at: 32, label: "Verifying citations against IndianKanoon…" },
  { at: 44, label: "Stripping unverified citations and building source map…" },
  { at: 52, label: "Persisting draft + audit log…" },
];

interface Props {
  // When true the card mounts and starts counting; when false it unmounts.
  // Owning component (DraftEmptyState / DraftTab) controls the lifecycle.
  busy: boolean;
  // Optional title — defaults to "Generating draft". Regenerate flow can
  // pass "Regenerating draft" so the partner knows the existing version is
  // being replaced rather than created from scratch.
  title?: string;
  eyebrow?: string;
}

export function DraftProgressCard({
  busy,
  title = "Reading the notice, drafting the reply, verifying citations",
  eyebrow = "Generating draft",
}: Props) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!busy) {
      setElapsed(0);
      return;
    }
    const start = Date.now();
    const id = setInterval(
      () => setElapsed(Math.round((Date.now() - start) / 1000)),
      250,
    );
    return () => clearInterval(id);
  }, [busy]);

  if (!busy) return null;

  const currentStep =
    STEPS.slice().reverse().find((s) => elapsed >= s.at) ?? STEPS[0];
  // 60s is the budget the brief commits to; show the bar relative to that.
  const pct = Math.min(95, Math.round((elapsed / 60) * 100));

  return (
    <div className="rounded-md border border-slate-line bg-white px-8 py-10">
      <p className="mb-1 text-[10px] font-bold uppercase tracking-[0.14em] text-gold-dark">
        {eyebrow}
      </p>
      <h2 className="mb-2 font-serif text-[24px] font-semibold text-navy-deep">
        {title}
      </h2>
      <p className="mb-6 max-w-[640px] font-serif text-[14px] italic text-slate">
        Typically completes in 45-120 seconds with Claude Opus on a real
        notice. The draft will appear automatically when ready &mdash; you
        don&rsquo;t need to wait on this screen.
      </p>

      <div className="mb-5 h-2 w-full overflow-hidden rounded-full bg-paper-tint">
        <div
          className="h-full bg-gold transition-all duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>

      <ul className="space-y-2">
        {STEPS.map((s) => {
          const done = elapsed > (STEPS[STEPS.indexOf(s) + 1]?.at ?? Infinity);
          const active = !done && s === currentStep;
          return (
            <li
              key={s.at}
              className={cn(
                "flex items-center gap-2.5 text-[13px]",
                done && "text-slate",
                active && "font-semibold text-ink",
                !done && !active && "text-slate-pale",
              )}
            >
              <span
                className={cn(
                  "flex h-4 w-4 items-center justify-center rounded-full border text-[10px]",
                  done && "border-success bg-success text-white",
                  active && "border-gold bg-gold/15 text-gold-dark",
                  !done && !active && "border-slate-line",
                )}
              >
                {done ? "✓" : active ? "…" : ""}
              </span>
              {s.label}
            </li>
          );
        })}
      </ul>

      <p className="mt-6 text-[11px] text-slate">
        Elapsed: <strong className="font-mono text-ink">{elapsed}s</strong>
      </p>
    </div>
  );
}
