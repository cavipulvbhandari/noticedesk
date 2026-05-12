"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { createNotice } from "@/lib/api";

interface Props {
  open: boolean;
  clientId: string;
  registrationId: string;
  law: "GST" | "IT";
  defaultPeriod?: string;
  onClose: () => void;
  onCreated: (noticeId: string) => void;
}

// Common GST + IT document types — matches the prototype's notice types.
const GST_TYPES = ["ASMT-10", "DRC-01", "DRC-01A", "DRC-03", "GST_HEARING"];
const IT_TYPES = [
  "IT_142(1)",
  "IT_143(2)",
  "IT_148_148A",
  "IT_CITA_NFAC_HEARING",
  "IT_245",
  "IT_154",
];

export function AddNoticeModal({
  open,
  clientId,
  registrationId,
  law,
  defaultPeriod,
  onClose,
  onCreated,
}: Props) {
  const types = law === "GST" ? GST_TYPES : IT_TYPES;
  const [documentType, setDocumentType] = useState<string>(types[0]!);
  const [period, setPeriod] = useState<string>(defaultPeriod ?? "");
  const [dueDate, setDueDate] = useState<string>("");
  const [authority, setAuthority] = useState<string>("");
  const [issue, setIssue] = useState<string>("");
  const [assignedTo, setAssignedTo] = useState<string>("");
  const [din, setDin] = useState<string>("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setDocumentType(types[0]!);
    setPeriod(defaultPeriod ?? "");
    setDueDate("");
    setAuthority("");
    setIssue("");
    setAssignedTo("");
    setDin("");
    setError(null);
    setBusy(false);
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !busy) onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, defaultPeriod]);

  if (!open) return null;

  async function handleSubmit() {
    if (!documentType.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const body: Parameters<typeof createNotice>[0] = {
        client_id: clientId,
        registration_id: registrationId,
        law,
        document_type: documentType.trim(),
      };
      if (period) {
        if (law === "GST") body.financial_year = period;
        else body.assessment_year = period;
      }
      if (dueDate) body.due_date = dueDate;
      if (authority.trim()) body.authority = authority.trim();
      if (issue.trim()) body.issue = issue.trim();
      if (assignedTo.trim()) body.assigned_to = assignedTo.trim();
      if (din.trim()) body.din_or_rfn = din.trim();
      const res = await createNotice(body);
      onCreated(res.notice_id);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "could not create notice");
      setBusy(false);
    }
  }

  const periodLabel = law === "GST" ? "Financial year" : "Assessment year";
  const periodPlaceholder = law === "GST" ? "2024-25" : "2024-25";

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Add a notice"
      className="fixed inset-0 z-[1000] flex items-center justify-center bg-navy-deep/55 p-5 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative max-h-[90vh] w-full max-w-[560px] overflow-y-auto rounded-lg bg-paper shadow-card-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="relative border-b border-slate-line px-7 py-5">
          <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-gold">
            Add notice manually
          </p>
          <h2 className="mt-1 font-serif text-[22px] font-semibold tracking-tight text-navy-deep">
            New {law} notice
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
            For partners who want to track a notice without uploading a PDF.
            The matter is auto-created if one doesn&rsquo;t already exist for
            this period.
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Field label="Type" required>
              <select value={documentType} onChange={(e) => setDocumentType(e.target.value)}>
                {types.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </Field>
            <Field label={periodLabel}>
              <input
                type="text"
                value={period}
                placeholder={periodPlaceholder}
                pattern="\d{4}-\d{2}"
                onChange={(e) => setPeriod(e.target.value)}
              />
            </Field>
            <Field label="Due date">
              <input
                type="date"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
              />
            </Field>
            <Field label="DIN / RFN">
              <input type="text" value={din} onChange={(e) => setDin(e.target.value)} />
            </Field>
            <div className="col-span-2">
              <Field label="Authority">
                <input
                  type="text"
                  value={authority}
                  placeholder="STO Range 5, Pune-1"
                  onChange={(e) => setAuthority(e.target.value)}
                />
              </Field>
            </div>
            <div className="col-span-2">
              <Field label="Issue / subject">
                <input
                  type="text"
                  value={issue}
                  placeholder="ITC mismatch FY 22-23, ₹14.2 lakh"
                  onChange={(e) => setIssue(e.target.value)}
                />
              </Field>
            </div>
            <Field label="Assigned to">
              <input
                type="text"
                value={assignedTo}
                placeholder="Rohan Mehta"
                onChange={(e) => setAssignedTo(e.target.value)}
              />
            </Field>
          </div>

          {error ? (
            <p className="mt-3 rounded border border-alarm/30 bg-alarm-bg px-3 py-2 text-sm text-alarm">
              {error}
            </p>
          ) : null}
        </div>

        <div className="flex items-center justify-end gap-2.5 border-t border-slate-line px-7 py-4">
          <Button variant="ghost" onClick={onClose} disabled={busy}>
            Cancel
          </Button>
          <Button variant="gold" onClick={handleSubmit} disabled={busy || !documentType.trim()}>
            {busy ? "Saving…" : "Add notice"}
          </Button>
        </div>
      </div>
    </div>
  );
}

function Field({
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
    <div>
      <label className="mb-1.5 block text-[11.5px] font-semibold tracking-wide text-slate">
        {label}
        {required ? <span className="ml-0.5 text-alarm">*</span> : null}
      </label>
      {enhanced}
    </div>
  );
}
