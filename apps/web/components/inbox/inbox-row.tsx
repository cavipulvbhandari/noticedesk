"use client";

import type { InboxItem } from "@noticedesk/shared/inbox";
import { FileText } from "lucide-react";

import { AnomalyActions } from "@/components/inbox/anomaly-actions";
import { Button } from "@/components/ui/button";
import { formatBytes, formatDateTime } from "@/lib/format";

import { ChannelChip } from "./channel-chip";
import { RoutingChip } from "./routing-chip";
import { OcrStatusChip } from "./status-chip";

interface InboxRowProps {
  item: InboxItem;
  onView: (item: InboxItem) => void;
  onResolved: () => void;
}

export function InboxRow({ item, onView, onResolved }: InboxRowProps) {
  const ocrReady = item.ocr_status === "completed";
  const hasAnomaly =
    item.routing_status !== "routed" &&
    item.routing_status !== "pending" &&
    item.parse_status === "completed";

  return (
    <li className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex min-w-0 items-start gap-3">
          <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-slate-100 text-slate-600">
            <FileText className="h-5 w-5" aria-hidden />
          </div>
          <div className="min-w-0">
            <p className="truncate font-medium text-navy">
              {item.original_filename}
              {item.document_type ? (
                <span className="ml-2 text-xs font-normal text-slate-500">
                  · {item.document_type}
                </span>
              ) : null}
            </p>
            <p className="mt-0.5 text-xs text-slate-500">
              {formatBytes(item.file_size_bytes)}
              {item.page_count ? ` · ${item.page_count} pages` : null}
              {" · "}
              {formatDateTime(item.uploaded_at)}
              {item.parse_confidence != null
                ? ` · ${(item.parse_confidence * 100).toFixed(0)}% confidence`
                : null}
            </p>
            {item.ocr_status === "failed" && item.ocr_error ? (
              <p className="mt-1 text-xs text-red-600">{item.ocr_error}</p>
            ) : null}
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2 sm:justify-end">
          <ChannelChip channel={item.ingest_channel} />
          <OcrStatusChip status={item.ocr_status} />
          <RoutingChip item={item} />
          <Button
            variant="ghost"
            size="sm"
            disabled={!ocrReady}
            onClick={() => onView(item)}
          >
            View OCR text
          </Button>
        </div>
      </div>
      {hasAnomaly ? (
        <div className="border-t border-slate-100 pt-3">
          {item.routing_status === "pan_gstin_mismatch" ? (
            <div className="mb-2 rounded border border-red-200 bg-red-50 p-2 text-xs text-red-700">
              The PAN and GSTIN on this document do not reconcile. Partner
              review required — no auto-fix.
            </div>
          ) : null}
          <AnomalyActions item={item} onResolved={onResolved} />
        </div>
      ) : null}
    </li>
  );
}
