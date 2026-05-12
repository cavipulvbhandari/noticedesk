"use client";

import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { addRegistration } from "@/lib/api";
import { cn } from "@/lib/cn";
import { stateNameFor } from "@/lib/states";

const GSTIN_RE = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]$/;

interface Props {
  open: boolean;
  clientId: string;
  clientLegalName: string;
  clientPan: string;
  onClose: () => void;
  onCreated: () => void;
}

interface Derivation {
  state_code: string | null;
  state_name: string | null;
  derived_pan: string | null;
  match: "match" | "mismatch" | "incomplete";
  helper: string;
  helperClass: "neutral" | "valid" | "invalid";
}

function deriveFromGstin(value: string, clientPan: string): Derivation {
  if (value.length === 0) {
    return {
      state_code: null,
      state_name: null,
      derived_pan: null,
      match: "incomplete",
      helper:
        "15 characters · positions 3 through 12 must equal the client's PAN. The system verifies this automatically.",
      helperClass: "neutral",
    };
  }
  if (value.length < 15) {
    return {
      state_code: value.slice(0, 2) || null,
      state_name: stateNameFor(value.slice(0, 2)),
      derived_pan: value.slice(2, 12) || null,
      match: "incomplete",
      helper: `${value.length} of 15 characters · format SSPPPPPPPPPP1Z9`,
      helperClass: "neutral",
    };
  }
  if (!GSTIN_RE.test(value)) {
    return {
      state_code: value.slice(0, 2),
      state_name: stateNameFor(value.slice(0, 2)),
      derived_pan: value.slice(2, 12),
      match: "mismatch",
      helper: "✗ Invalid GSTIN format. Expected 2 digits + 5 letters + 4 digits + 1 letter + 1 alphanumeric + Z + 1 alphanumeric.",
      helperClass: "invalid",
    };
  }
  const derived = value.slice(2, 12);
  if (derived === clientPan) {
    return {
      state_code: value.slice(0, 2),
      state_name: stateNameFor(value.slice(0, 2)),
      derived_pan: derived,
      match: "match",
      helper: "✓ Valid GSTIN · PAN reconciled against client.",
      helperClass: "valid",
    };
  }
  return {
    state_code: value.slice(0, 2),
    state_name: stateNameFor(value.slice(0, 2)),
    derived_pan: derived,
    match: "mismatch",
    helper: `✗ Positions 3–12 derive ${derived}, which is a different PAN.`,
    helperClass: "invalid",
  };
}

export function AddGstModal({
  open,
  clientId,
  clientLegalName,
  clientPan,
  onClose,
  onCreated,
}: Props) {
  const [gstin, setGstin] = useState("");
  const [jurisdiction, setJurisdiction] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setGstin("");
      setJurisdiction("");
      setSubmitError(null);
      setSubmitting(false);
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !submitting) onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose, submitting]);

  const derivation = useMemo(() => deriveFromGstin(gstin, clientPan), [gstin, clientPan]);
  const canSave = derivation.match === "match" && !submitting;

  async function handleSubmit() {
    if (!canSave) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      await addRegistration(clientId, {
        client_id: clientId,
        registration_type: "GST",
        identifier_value: gstin,
        state_code: derivation.state_code,
        state_name: derivation.state_name,
      });
      onCreated();
    } catch (e: unknown) {
      setSubmitError(e instanceof Error ? e.message : "could not add registration");
      setSubmitting(false);
    }
  }

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Add a state GSTIN"
      className="fixed inset-0 z-[1000] flex items-center justify-center bg-navy-deep/55 p-5 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative max-h-[90vh] w-full max-w-[520px] overflow-y-auto rounded-lg bg-paper shadow-card-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="relative border-b border-slate-line px-7 py-5">
          <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-gold">
            Add GST registration
          </p>
          <h2 className="mt-1 font-serif text-[22px] font-semibold tracking-tight text-navy-deep">
            Add a state GSTIN
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
          <div className="mb-5 rounded-sm bg-paper-tint px-3.5 py-2.5 text-[12px] text-slate">
            Client:{" "}
            <strong className="font-semibold text-ink">{clientLegalName}</strong> · PAN{" "}
            <span className="font-mono text-[12px] text-ink">{clientPan}</span>
          </div>

          <div className="mb-4">
            <label className="mb-1.5 block text-[11.5px] font-semibold tracking-wide text-slate">
              GSTIN <span className="text-alarm">*</span>
            </label>
            <input
              type="text"
              autoFocus
              value={gstin}
              maxLength={15}
              placeholder="27AAACX1234F1Z5"
              onChange={(e) => setGstin(e.target.value.toUpperCase())}
              className="h-10 w-full rounded-sm border border-slate-line bg-white px-3.5 py-2 font-mono uppercase text-[14px] tracking-wider text-ink outline-none focus:border-gold"
            />
            <p
              className={cn(
                "mt-1.5 text-[11.5px] leading-snug",
                derivation.helperClass === "valid" && "font-medium text-success",
                derivation.helperClass === "invalid" && "font-medium text-alarm",
                derivation.helperClass === "neutral" && "font-serif italic text-slate",
              )}
            >
              {derivation.helper}
            </p>

            {gstin.length > 0 ? (
              <div className="mt-3 rounded-sm border border-gold/30 bg-paper-warm px-3.5 py-2.5 font-mono text-[11.5px] leading-relaxed text-ink">
                <DerivationRow label="GSTIN entered" value={gstin || "—"} />
                <DerivationRow
                  label="State (positions 1–2)"
                  value={
                    derivation.state_code
                      ? `${derivation.state_code} · ${derivation.state_name ?? "Unknown"}`
                      : "—"
                  }
                />
                <DerivationRow
                  label="PAN derived (positions 3–12)"
                  value={derivation.derived_pan ?? "—"}
                />
                <DerivationRow label="Client's PAN" value={clientPan} />
                <div className="mt-1.5 flex items-center justify-between border-t border-dashed border-gold/40 pt-1.5">
                  <span className="font-semibold text-gold-dark">Reconciliation</span>
                  <span
                    className={cn(
                      "font-bold",
                      derivation.match === "match" && "text-success",
                      derivation.match === "mismatch" && "text-alarm",
                      derivation.match === "incomplete" && "text-slate",
                    )}
                  >
                    {derivation.match === "match"
                      ? "✓ MATCH"
                      : derivation.match === "mismatch"
                        ? "✗ MISMATCH"
                        : "…"}
                  </span>
                </div>
              </div>
            ) : null}
          </div>

          <div className="mb-2">
            <label className="mb-1.5 block text-[11.5px] font-semibold tracking-wide text-slate">
              Jurisdiction office (optional)
            </label>
            <input
              type="text"
              value={jurisdiction}
              placeholder="STO Range 5, Pune-1"
              onChange={(e) => setJurisdiction(e.target.value)}
              className="h-10 w-full rounded-sm border border-slate-line bg-white px-3.5 py-2 text-[14px] text-ink outline-none focus:border-gold"
            />
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
            {submitting ? "Saving…" : "Save registration"}
          </Button>
        </div>
      </div>
    </div>
  );
}

function DerivationRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-0.5">
      <span className="text-[10.5px] uppercase tracking-[0.04em] text-slate">{label}</span>
      <span className="font-semibold tracking-wider text-navy-deep">{value}</span>
    </div>
  );
}
