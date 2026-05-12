"use client";

import { useEffect } from "react";

import { Button } from "@/components/ui/button";

interface Props {
  open: boolean;
  title: string;
  eyebrow?: string;
  children: React.ReactNode;
  onClose: () => void;
  ctaLabel?: string;
}

// A small read-only modal used for "this feature arrives in Phase 2" surfaces:
// Sync now / Connect portal / Import from Excel detail. Looks like the
// prototype's empty-confirmation pattern, just with a single Close action.
export function InfoModal({
  open,
  title,
  eyebrow,
  children,
  onClose,
  ctaLabel = "Got it",
}: Props) {
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
      aria-label={title}
      className="fixed inset-0 z-[1000] flex items-center justify-center bg-navy-deep/55 p-5 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative max-h-[90vh] w-full max-w-[480px] overflow-y-auto rounded-lg bg-paper shadow-card-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="relative border-b border-slate-line px-7 py-5">
          {eyebrow ? (
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-gold">
              {eyebrow}
            </p>
          ) : null}
          <h2 className="mt-1 font-serif text-[22px] font-semibold tracking-tight text-navy-deep">
            {title}
          </h2>
          <button
            type="button"
            aria-label="Close"
            onClick={onClose}
            className="absolute right-5 top-5 flex h-7 w-7 items-center justify-center rounded-full text-slate transition-colors hover:bg-paper-tint hover:text-ink"
          >
            ✕
          </button>
        </div>
        <div className="px-7 py-6 font-serif text-[14px] leading-relaxed text-ink-soft">
          {children}
        </div>
        <div className="flex justify-end border-t border-slate-line px-7 py-4">
          <Button variant="primary" size="sm" onClick={onClose}>
            {ctaLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}
