"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { updateClient, type ClientDetail } from "@/lib/api";

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
  client: ClientDetail;
  onClose: () => void;
  onSaved: () => void;
}

export function EditClientModal({ open, client, onClose, onSaved }: Props) {
  const [legalName, setLegalName] = useState(client.legal_name);
  const [tradeName, setTradeName] = useState(client.trade_name ?? "");
  const [entityType, setEntityType] = useState(client.entity_type ?? ENTITY_TYPES[0]!);
  const [industry, setIndustry] = useState(client.industry ?? "");
  const [email, setEmail] = useState(client.email ?? "");
  const [phone, setPhone] = useState(client.phone ?? "");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setLegalName(client.legal_name);
      setTradeName(client.trade_name ?? "");
      setEntityType(client.entity_type ?? ENTITY_TYPES[0]!);
      setIndustry(client.industry ?? "");
      setEmail(client.email ?? "");
      setPhone(client.phone ?? "");
      setError(null);
      setSubmitting(false);
    }
  }, [open, client]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !submitting) onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose, submitting]);

  if (!open) return null;

  async function handleSubmit() {
    if (legalName.trim().length === 0) return;
    setSubmitting(true);
    setError(null);
    try {
      await updateClient(client.client_id, {
        legal_name: legalName.trim(),
        trade_name: tradeName.trim() || null,
        entity_type: entityType,
        industry: industry.trim() || null,
        email: email.trim() || null,
        phone: phone.trim() || null,
      });
      onSaved();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "update failed");
      setSubmitting(false);
    }
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Edit client"
      className="fixed inset-0 z-[1000] flex items-center justify-center bg-navy-deep/55 p-5 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative max-h-[90vh] w-full max-w-[520px] overflow-y-auto rounded-lg bg-paper shadow-card-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="relative border-b border-slate-line px-7 py-5">
          <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-gold">
            Edit client
          </p>
          <h2 className="mt-1 font-serif text-[22px] font-semibold tracking-tight text-navy-deep">
            Edit client details
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
            PAN cannot be changed once set &mdash; it&rsquo;s the canonical identifier. Current PAN:{" "}
            <span className="font-mono text-[12px] text-ink">{client.pan}</span>
          </div>

          <FormField label="Legal name" required>
            <input
              type="text"
              value={legalName}
              onChange={(e) => setLegalName(e.target.value)}
            />
          </FormField>

          <FormField label="Trade name">
            <input
              type="text"
              value={tradeName}
              onChange={(e) => setTradeName(e.target.value)}
            />
          </FormField>

          <FormField label="Entity type">
            <select value={entityType} onChange={(e) => setEntityType(e.target.value)}>
              {ENTITY_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </FormField>

          <FormField label="Industry">
            <input
              type="text"
              value={industry}
              onChange={(e) => setIndustry(e.target.value)}
            />
          </FormField>

          <FormField label="Client email (for checklist + replies)">
            <input
              type="email"
              value={email}
              placeholder="finance@acme.in"
              onChange={(e) => setEmail(e.target.value)}
            />
          </FormField>

          <FormField label="Client phone (optional)">
            <input
              type="tel"
              value={phone}
              placeholder="+91 98xxxxxxxx"
              onChange={(e) => setPhone(e.target.value)}
            />
          </FormField>

          {error ? (
            <p className="mt-3 rounded border border-alarm/30 bg-alarm-bg px-3 py-2 text-sm text-alarm">
              {error}
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
            disabled={submitting || legalName.trim().length === 0}
          >
            {submitting ? "Saving…" : "Save changes"}
          </Button>
        </div>
      </div>
    </div>
  );
}

function FormField({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactElement<{ className?: string }>;
}) {
  const baseClass =
    "h-10 w-full rounded-sm border border-slate-line bg-white px-3.5 py-2 text-[14px] text-ink outline-none focus:border-gold";
  const child = children;
  const merged = `${baseClass}${child.props.className ? " " + child.props.className : ""}`;
  const enhanced = { ...child, props: { ...child.props, className: merged } };
  return (
    <div className="mb-4">
      <label className="mb-1.5 block text-[11.5px] font-semibold tracking-wide text-slate">
        {label}
        {required ? <span className="ml-0.5 text-alarm">*</span> : null}
      </label>
      {enhanced}
    </div>
  );
}
