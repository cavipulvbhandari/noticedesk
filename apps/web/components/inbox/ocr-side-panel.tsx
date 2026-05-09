"use client";

import type { InboxItem } from "@noticedesk/shared/inbox";
import { useEffect, useState } from "react";

import { Dialog } from "@/components/ui/dialog";
import { fetchOcrText, type OcrTextResponse } from "@/lib/api";

interface Props {
  item: InboxItem | null;
  onClose: () => void;
}

export function OcrSidePanel({ item, onClose }: Props) {
  const [data, setData] = useState<OcrTextResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!item) {
      setData(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchOcrText(item.inbox_id)
      .then((d) => {
        if (!cancelled) setData(d);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "failed to load");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [item]);

  return (
    <Dialog
      open={item !== null}
      onClose={onClose}
      title={item?.original_filename ?? "OCR text"}
      className="max-w-3xl"
    >
      {loading ? (
        <p className="text-sm text-slate-500">Loading…</p>
      ) : error ? (
        <p className="text-sm text-red-600">{error}</p>
      ) : data ? (
        <div className="space-y-3">
          <div className="text-xs text-slate-500">
            Provider: {data.ocr_provider_used ?? "—"} · Pages:{" "}
            {data.page_count ?? "—"}
          </div>
          <pre className="max-h-[60vh] overflow-auto rounded border border-slate-200 bg-slate-50 p-3 text-xs text-slate-800 whitespace-pre-wrap">
            {data.ocr_text ?? "(no OCR text)"}
          </pre>
        </div>
      ) : null}
    </Dialog>
  );
}
