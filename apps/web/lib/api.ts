// Browser-side API client. The Next.js dev session cookie is read on the
// server only, so client components proxy through Next.js route handlers
// (under app/api/*) rather than calling the FastAPI directly. Server
// components fetch the API directly.

import type {
  InboxList,
  OcrTextResponse,
  UploadResponse,
} from "@noticedesk/shared/inbox";

export type { InboxItem, InboxList, UploadResponse, OcrTextResponse } from "@noticedesk/shared/inbox";

export async function fetchInbox(): Promise<InboxList> {
  const res = await fetch("/api/inbox", { cache: "no-store" });
  if (!res.ok) throw new Error(`failed to load inbox (${res.status})`);
  return (await res.json()) as InboxList;
}

export async function uploadDocument(
  file: File,
  ingestChannel: "web_upload" | "mobile_capture",
  onProgress?: (pct: number) => void,
): Promise<UploadResponse> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `/api/upload?ingest_channel=${ingestChannel}`);
    xhr.responseType = "json";
    if (onProgress) {
      xhr.upload.addEventListener("progress", (e) => {
        if (e.lengthComputable) onProgress((e.loaded / e.total) * 100);
      });
    }
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(xhr.response as UploadResponse);
      } else {
        reject(
          new Error(
            (xhr.response as { error?: { message?: string } })?.error?.message ??
              `upload failed (${xhr.status})`,
          ),
        );
      }
    };
    xhr.onerror = () => reject(new Error("network error during upload"));
    const fd = new FormData();
    fd.append("file", file);
    xhr.send(fd);
  });
}

export async function fetchOcrText(inboxId: string): Promise<OcrTextResponse> {
  const res = await fetch(`/api/ocr/${inboxId}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`failed to load OCR text (${res.status})`);
  return (await res.json()) as OcrTextResponse;
}
