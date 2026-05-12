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

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let detail = "";
    try {
      const j = (await res.json()) as { error?: { message?: string } };
      detail = j?.error?.message ?? "";
    } catch {
      // ignore
    }
    throw new Error(detail || `request failed (${res.status})`);
  }
  return (await res.json()) as T;
}

export interface ManualRouteBody {
  client_id: string;
  registration_id: string;
  override_reason: string;
}

export function routeManually(
  inboxId: string,
  body: ManualRouteBody,
): Promise<{ inbox_id: string; routing_status: string }> {
  return postJson(`/api/route-manually/${inboxId}`, body);
}

export function rejectInbox(
  inboxId: string,
  reason: string,
): Promise<{ status: string }> {
  return postJson(`/api/reject/${inboxId}`, { reason });
}

export interface AddClientBody {
  pan: string;
  legal_name: string;
  trade_name?: string | null;
  entity_type?: string | null;
  industry?: string | null;
  auto_route_inbox_id?: string | null;
}

export function addClient(body: AddClientBody): Promise<{ client_id: string }> {
  return postJson("/api/clients", body);
}

export interface ClientSummary {
  client_id: string;
  pan: string;
  legal_name: string;
  trade_name: string | null;
  entity_type: string | null;
  industry: string | null;
  gst_count: number;
  gst_state_codes: string[];
  active_it_count: number;
  active_gst_count: number;
  earliest_open_due_date: string | null;
}

export interface ClientList {
  clients: ClientSummary[];
  total: number;
}

export async function fetchClients(): Promise<ClientList> {
  const res = await fetch("/api/clients", { cache: "no-store" });
  if (!res.ok) throw new Error(`failed to load clients (${res.status})`);
  return (await res.json()) as ClientList;
}

export interface ClientRegistration {
  registration_id: string;
  registration_type: "IT" | "GST";
  identifier_value: string;
  state_code: string | null;
  state_name: string | null;
  jurisdiction_office: string | null;
  registration_status: string | null;
  active_notice_count: number;
  earliest_open_due_date: string | null;
  sync_method: "manual" | "portal";
  last_synced_at: string | null;
}

export interface ClientDetail {
  client_id: string;
  pan: string;
  legal_name: string;
  trade_name: string | null;
  entity_type: string | null;
  cin: string | null;
  date_of_incorporation_or_birth: string | null;
  industry: string | null;
  registrations: ClientRegistration[];
}

export async function fetchClient(id: string): Promise<ClientDetail> {
  const res = await fetch(`/api/clients/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`failed to load client (${res.status})`);
  return (await res.json()) as ClientDetail;
}

export interface UpdateClientBody {
  legal_name?: string;
  trade_name?: string | null;
  entity_type?: string | null;
  industry?: string | null;
  cin?: string | null;
}

export async function updateClient(
  id: string,
  body: UpdateClientBody,
): Promise<{ client_id: string; updated_fields: string[] }> {
  const res = await fetch(`/api/clients/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const j = (await res.json().catch(() => null)) as { error?: { message?: string } } | null;
    throw new Error(j?.error?.message ?? `update failed (${res.status})`);
  }
  return (await res.json()) as { client_id: string; updated_fields: string[] };
}

export async function deleteClient(id: string): Promise<{ deleted: true }> {
  const res = await fetch(`/api/clients/${id}`, { method: "DELETE" });
  if (!res.ok) {
    const j = (await res.json().catch(() => null)) as { error?: { message?: string } } | null;
    throw new Error(j?.error?.message ?? `delete failed (${res.status})`);
  }
  return (await res.json()) as { deleted: true };
}

export interface AddRegistrationBody {
  client_id: string;
  registration_type: "IT" | "GST";
  identifier_value: string;
  state_code?: string | null;
  state_name?: string | null;
  auto_route_inbox_id?: string | null;
}

export function addRegistration(
  clientId: string,
  body: AddRegistrationBody,
): Promise<{ registration_id: string }> {
  return postJson(`/api/registrations/${clientId}`, body);
}
