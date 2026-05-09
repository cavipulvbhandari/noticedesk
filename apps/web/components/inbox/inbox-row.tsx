"use client";

import type { InboxItem } from "@noticedesk/shared/inbox";
import { FileText } from "lucide-react";

import { Button } from "@/components/ui/button";
import { formatBytes, formatDateTime } from "@/lib/format";

import { ChannelChip } from "./channel-chip";
import { OcrStatusChip } from "./status-chip";

interface InboxRowProps {
  item: InboxItem;
  onView: (item: InboxItem) => void;
}

export function InboxRow({ item, onView }: InboxRowProps) {
  const ocrReady = item.ocr_status === "completed";
  return (
    <li className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white p-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex min-w-0 items-start gap-3">
        <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-slate-100 text-slate-600">
          <FileText className="h-5 w-5" aria-hidden />
        </div>
        <div className="min-w-0">
          <p className="truncate font-medium text-navy">
            {item.original_filename}
          </p>
          <p className="mt-0.5 text-xs text-slate-500">
            {formatBytes(item.file_size_bytes)}
            {item.page_count ? ` · ${item.page_count} pages` : null}
            {" · "}
            {formatDateTime(item.uploaded_at)}
          </p>
          {item.ocr_status === "failed" && item.ocr_error ? (
            <p className="mt-1 text-xs text-red-600">{item.ocr_error}</p>
          ) : null}
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2 sm:justify-end">
        <ChannelChip channel={item.ingest_channel} />
        <OcrStatusChip status={item.ocr_status} />
        <Button
          variant="ghost"
          size="sm"
          disabled={!ocrReady}
          onClick={() => onView(item)}
        >
          View OCR text
        </Button>
      </div>
    </li>
  );
}
