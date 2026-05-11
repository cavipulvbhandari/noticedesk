"use client";

import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { addClient } from "@/lib/api";
import { cn } from "@/lib/cn";

const PAN_RE = /^[A-Z]{5}[0-9]{4}[A-Z]$/;

const ENTITY_TYPES = [
  "Private Limited Company",
  "Public Limited Company",
  "Limited Liability Partnership",
  "Partnership Firm",
  "Individual (Proprietor)",
  "HUF",
  "Trust",
  "AOP / BOI",
  "Society",
];

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: (clientId: string) => void;
}

type PanState =
  | { kind: "empty" }
  | { kind: "partial"; len: number }
  | { kind: "valid" }
  | { kind: "invalid" };

function panStateFor(value: string): PanState {
  if (value.length === 0) return { kind: "empty" };
  if (value.length < 10) return { kind: "partial", len: value.length };
  if (PAN_RE.test(value)) return { kind: "valid" };
  return { kind: "invalid" };
}

export function AddClientModal({ open, onClose, onCreated }: Props) {
  const [pan, setPan] = useState("");
  const [legalName, setLegalName] = useState("");
  const [entityType, setEntityType] = useState<string>(ENTITY_TYPES[0]!);
  const [industry, setIndustry] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Reset form whenever the modal re-opens. Stale half-typed PANs from a
  // previous attempt are confusing.
  useEffect(() => {
    if (open) {
      setPan("");
      setLegalName("");
      setEntityType(ENTITY_TYPES[0]!);
      setIndustry("");
      setSubmitError(null);
      setSubmitting(false);
    }
  }, [open]);

  const panState = useMemo(() => panStateFor(pan), [pan]);
  const canSave = panState.kind === "valid" && legalName.trim().length > 0 && !submitting;

  async function handleSubmit() {
    if (!canSave) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      const res = await addClient({
        pan,
        legal_name: legalName.trim(),
        entity_type: entityType,
        industry: industry.trim() || null,
      });
      onCreated(res.client_id);
    } catch (e: unknown) {
      setSubmitError(e instanceof Error ? e.message : "could not add client");
      setSubmitting(false);
    }
  }

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !submitting) onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose, submitting]);

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Add a new client"
      className="fixed inset-0 z-[1000] flex items-center justify-center bg-navy-deep/55 p-5 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative max-h-[90vh] w-full max-w-[520px] overflow-y-auto rounded-lg bg-paper shadow-card-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="relative border-b border-slate-line px-7 py-5">
          <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-gold">
            Add client
          </p>
          <h2 className="mt-1 font-serif text-[22px] font-semibold tracking-tight text-navy-deep">
            Add a new client
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

        <div className="px-7 py-6">
          <Field
            label="PAN"
            required
            help={<PanHelp state={panState} />}
          >
            <input
              type="text"
              autoFocus
              value={pan}
              maxLength={10}
              placeholder="AAACX1234F"
              onChange={(e) => setPan(e.target.value.toUpperCase())}
              className="font-mono uppercase tracking-wider"
            />
          </Field>

          <Field label="Legal name" required>
            <input
              type="text"
              value={legalName}
              placeholder="ABC Industries Pvt Ltd"
              onChange={(e) => setLegalName(e.target.value)}
            />
          </Field>

          <Field label="Entity type" required>
            <select
              value={entityType}
              onChange={(e) => setEntityType(e.target.value)}
            >
              {ENTITY_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Industry">
            <input
              type="text"
              value={industry}
              placeholder="Manufacturing"
              onChange={(e) => setIndustry(e.target.value)}
            />
          </Field>

          <div className="mt-4 rounded-sm border-l-[3px] border-gold bg-paper-warm px-3.5 py-3 text-[12px] leading-relaxed text-ink-soft">
            <p className="mb-1 text-[10px] font-bold uppercase tracking-[0.12em] text-gold-dark">
              Auto-created
            </p>
            One Income Tax registration will be created automatically using the PAN as
            identifier. Add GST registrations from the client detail view after saving.
          </div>

          {submitError ? (
            <p className="mt-3 rounded border border-alarm/30 bg-alarm-bg px-3 py-2 text-sm text-alarm">
              {submitError}
            </p>
          ) : null}
        </div>

        <div className="flex items-center justify-end gap-2.5 border-t border-slate-line px-7 py-4">
          <Button variant="ghost" onClick={onClose} disabled={submitting}>
            Cancel
          </Button>
          <Button
            variant="gold"
            onClick={handleSubmit}
            disabled={!canSave}
            className={cn(!canSave && "cursor-not-allowed opacity-40")}
          >
            {submitting ? "Saving…" : "Save client"}
          </Button>
        </div>
      </div>
    </div>
  );
}

function Field({
  label,
  required,
  help,
  children,
}: {
  label: string;
  required?: boolean;
  help?: React.ReactNode;
  children: React.ReactElement<{ className?: string }>;
}) {
  const baseClass =
    "h-10 w-full rounded-sm border border-slate-line bg-white px-3.5 py-2 text-sm text-ink outline-none transition-colors placeholder:text-slate-pale focus:border-gold";
  // Merge our base class onto the input/select while preserving anything
  // the caller already passed (the PAN field adds font-mono).
  const child = children as React.ReactElement<{ className?: string }>;
  const merged = cn(baseClass, child.props.className);
  const enhanced = { ...child, props: { ...child.props, className: merged } };

  return (
    <div className="mb-4">
      <label className="mb-1.5 block text-[11.5px] font-semibold tracking-wide text-slate">
        {label}
        {required ? <span className="ml-0.5 text-alarm">*</span> : null}
      </label>
      {enhanced}
      {help ? <div className="mt-1.5 text-[11.5px] leading-snug">{help}</div> : null}
    </div>
  );
}

function PanHelp({ state }: { state: PanState }) {
  if (state.kind === "empty") {
    return (
      <span className="font-serif italic text-slate">
        10-character PAN · format AAAAA9999A. This is the canonical client identifier —
        once set, it cannot be changed.
      </span>
    );
  }
  if (state.kind === "partial") {
    return (
      <span className="font-serif italic text-slate">
        {state.len} of 10 characters · format AAAAA9999A
      </span>
    );
  }
  if (state.kind === "valid") {
    return (
      <span className="font-medium text-success">✓ Valid PAN format · ready to save</span>
    );
  }
  return (
    <span className="font-medium text-alarm">
      ✗ Invalid PAN format. Expected 5 letters + 4 digits + 1 letter.
    </span>
  );
}
