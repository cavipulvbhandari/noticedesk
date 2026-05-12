"use client";

import { Upload } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast";
import {
  fetchMatterDocuments,
  updateDocument,
  uploadMatterDocument,
  type DocumentLifecycle,
  type MatterDocument,
  type NoticeDetail,
} from "@/lib/api";
import { cn } from "@/lib/cn";

interface Props {
  data: NoticeDetail;
}

const LIFECYCLE_OPTIONS: Array<{ value: DocumentLifecycle; label: string }> = [
  { value: "requested", label: "Requested from client" },
  { value: "received", label: "Received" },
  { value: "validated", label: "Validated" },
  { value: "used_in_draft", label: "Used in draft" },
  { value: "approved", label: "Approved" },
  { value: "submitted", label: "Submitted" },
  { value: "acknowledged", label: "Acknowledged" },
  { value: "referenced_in_appeal", label: "Referenced in appeal" },
];

const LIFECYCLE_TONE: Record<DocumentLifecycle, string> = {
  requested: "bg-slate-100 text-slate",
  received: "bg-paper-tint text-ink",
  validated: "bg-success-bg text-success",
  used_in_draft: "bg-gold/20 text-gold-dark",
  approved: "bg-success-bg text-success",
  submitted: "bg-navy/10 text-navy",
  acknowledged: "bg-success/20 text-success",
  referenced_in_appeal: "bg-gold/30 text-gold-dark",
};

export function DocumentsTab({ data }: Props) {
  const matterId = data.notice.matter_id;
  const sourceInbox = data.notice.source_inbox_id;
  const { toast } = useToast();
  const [docs, setDocs] = useState<MatterDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [drag, setDrag] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const load = useCallback(async () => {
    try {
      const res = await fetchMatterDocuments(matterId);
      setDocs(res.documents);
    } catch (e: unknown) {
      toast(e instanceof Error ? e.message : "failed to load documents", "error");
    } finally {
      setLoading(false);
    }
  }, [matterId, toast]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleUpload(files: FileList | null) {
    if (!files || files.length === 0) return;
    setUploading(true);
    try {
      for (const f of Array.from(files)) {
        await uploadMatterDocument(matterId, f, "supporting");
      }
      toast(
        `Uploaded ${files.length} document${files.length === 1 ? "" : "s"}`,
        "success",
      );
      await load();
    } catch (e: unknown) {
      toast(e instanceof Error ? e.message : "upload failed", "error");
    } finally {
      setUploading(false);
    }
  }

  async function handleLifecycle(doc: MatterDocument, next: DocumentLifecycle) {
    try {
      await updateDocument(doc.document_id, { lifecycle_stage: next });
      toast(`Marked "${doc.filename}" as ${next.replace(/_/g, " ")}`, "success");
      await load();
    } catch (e: unknown) {
      toast(e instanceof Error ? e.message : "update failed", "error");
    }
  }

  return (
    <div className="overflow-hidden rounded-md border border-slate-line bg-white">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-line bg-paper px-5 py-3.5">
        <h3 className="font-serif text-[15px] font-semibold text-navy-deep">Documents</h3>
        <div className="flex items-center gap-2">
          <input
            ref={inputRef}
            type="file"
            multiple
            className="sr-only"
            onChange={(e) => void handleUpload(e.target.files)}
          />
          <Button
            variant="gold"
            size="sm"
            onClick={() => inputRef.current?.click()}
            disabled={uploading}
          >
            <Upload className="mr-1.5 h-3.5 w-3.5" aria-hidden />
            {uploading ? "Uploading…" : "Upload"}
          </Button>
        </div>
      </header>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
          void handleUpload(e.dataTransfer.files);
        }}
        className={cn(
          "border-b border-dashed border-slate-line bg-paper-warm/30 px-5 py-4 text-center text-[12.5px] transition-colors",
          drag && "border-gold bg-paper-warm",
        )}
      >
        <p className="font-serif italic text-slate">
          Drop PDFs, images, or working papers here — they attach to this
          matter and become available to the drafting agent.
        </p>
      </div>

      {sourceInbox ? (
        <div className="border-b border-slate-line px-5 py-3 text-[12.5px] text-slate">
          Original notice routed from inbox{" "}
          <span className="font-mono text-[11px] text-ink">{sourceInbox}</span>.
        </div>
      ) : null}

      {loading ? (
        <p className="px-5 py-8 text-center font-serif italic text-slate">Loading…</p>
      ) : docs.length === 0 ? (
        <p className="px-5 py-10 text-center font-serif italic text-slate">
          No documents attached yet. Drop files above or click Upload.
        </p>
      ) : (
        <table className="w-full border-collapse">
          <thead>
            <tr>
              <Th>Filename</Th>
              <Th>Type</Th>
              <Th>Lifecycle</Th>
              <Th>Size</Th>
              <Th>Uploaded</Th>
            </tr>
          </thead>
          <tbody>
            {docs.map((d) => (
              <tr key={d.document_id} className="border-b border-slate-line last:border-b-0">
                <Td>
                  <span className="font-medium text-ink">{d.filename}</span>
                </Td>
                <Td>{d.document_type ?? "—"}</Td>
                <Td>
                  <LifecyclePicker doc={d} onChange={(v) => void handleLifecycle(d, v)} />
                </Td>
                <Td>{d.size_bytes ? formatBytes(d.size_bytes) : "—"}</Td>
                <Td>
                  <div>{d.uploaded_at ? new Date(d.uploaded_at).toLocaleString("en-IN") : "—"}</div>
                  {d.uploaded_by_name ? (
                    <div className="mt-0.5 text-[11px] text-slate">by {d.uploaded_by_name}</div>
                  ) : null}
                </Td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function LifecyclePicker({
  doc,
  onChange,
}: {
  doc: MatterDocument;
  onChange: (next: DocumentLifecycle) => void;
}) {
  const current = doc.lifecycle_stage ?? "received";
  return (
    <div className="flex items-center gap-2">
      <span
        className={cn(
          "rounded-full px-2 py-0.5 text-[10.5px] font-bold uppercase tracking-wide",
          LIFECYCLE_TONE[current],
        )}
      >
        {current.replace(/_/g, " ")}
      </span>
      <select
        value={current}
        onChange={(e) => onChange(e.target.value as DocumentLifecycle)}
        className="rounded-sm border border-slate-line bg-white px-2 py-0.5 text-[11px]"
        aria-label="Change lifecycle stage"
      >
        {LIFECYCLE_OPTIONS.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return (
    <th className="border-b border-slate-line bg-paper px-4 py-3 text-left text-[10.5px] font-semibold uppercase tracking-[0.06em] text-slate">
      {children}
    </th>
  );
}

function Td({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <td className={`px-4 py-3 align-middle text-[13px] text-ink-soft ${className}`}>{children}</td>
  );
}

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}
