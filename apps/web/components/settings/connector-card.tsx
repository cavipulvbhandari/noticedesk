"use client";

import { cn } from "@/lib/cn";

export type ConnectorStatus = "connected" | "available" | "coming-soon";

interface Props {
  iconLabel: string;
  iconClassName: string;
  name: string;
  description: React.ReactNode;
  meta: Array<{ label: string; value: string }>;
  status: ConnectorStatus;
  statusLabel: string;
  ctaLabel?: string;
  ctaDisabled?: boolean;
  onCta?: () => void;
  faded?: boolean;
}

const STATUS_TONE: Record<ConnectorStatus, string> = {
  "connected": "bg-success/20 text-success",
  "available": "bg-success/15 text-success",
  "coming-soon": "bg-paper-tint text-slate",
};

export function ConnectorCard({
  iconLabel,
  iconClassName,
  name,
  description,
  meta,
  status,
  statusLabel,
  ctaLabel,
  ctaDisabled,
  onCta,
  faded,
}: Props) {
  return (
    <div
      className={cn(
        "mb-4 grid grid-cols-[auto_1fr_auto] items-center gap-5 rounded-md border border-slate-line bg-white px-6 py-5",
        faded && "opacity-70",
      )}
    >
      <div
        className={cn(
          "flex h-14 w-14 items-center justify-center rounded-md font-serif text-[22px] font-bold",
          iconClassName,
        )}
      >
        {iconLabel}
      </div>
      <div>
        <h4 className="font-serif text-[17px] font-semibold text-navy-deep">{name}</h4>
        <p className="mt-1 text-[12.5px] leading-relaxed text-slate">{description}</p>
        {meta.length > 0 ? (
          <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 font-mono text-[11px] text-slate-soft">
            {meta.map((m) => (
              <span key={m.label}>
                <strong className="font-sans font-semibold text-ink">{m.label}:</strong>{" "}
                {m.value}
              </span>
            ))}
          </div>
        ) : null}
      </div>
      <div className="flex flex-col items-end gap-2">
        <span
          className={cn(
            "rounded-full px-2.5 py-1 text-[10.5px] font-bold uppercase tracking-[0.1em]",
            STATUS_TONE[status],
          )}
        >
          {statusLabel}
        </span>
        {ctaLabel ? (
          <button
            type="button"
            disabled={ctaDisabled}
            onClick={onCta}
            className={cn(
              "rounded-sm border border-slate-line bg-white px-3 py-1 text-[12px] font-semibold text-ink transition-colors hover:border-slate hover:bg-paper",
              ctaDisabled && "cursor-not-allowed opacity-60",
            )}
          >
            {ctaLabel}
          </button>
        ) : null}
      </div>
    </div>
  );
}
