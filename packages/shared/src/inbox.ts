// Sprint 2: shared inbox types. Mirror the documents_inbox table and the
// Pydantic models in apps/api/app/models/inbox.py.

export type OcrStatus = "pending" | "in_progress" | "completed" | "failed";

export type ParseStatus =
  | "pending"
  | "in_progress"
  | "completed"
  | "failed"
  | "needs_review";

export type RoutingStatus =
  | "pending"
  | "routed"
  | "client_not_found"
  | "new_gst_registration_detected"
  | "pan_gstin_mismatch"
  | "no_identifier_found"
  | "manual_assignment";

export type IngestChannel =
  | "web_upload"
  | "mobile_capture"
  | "email"
  | "gst_portal_gsp"
  | "it_portal_aa"
  | "whatsapp";

export interface InboxItem {
  inbox_id: string;
  original_filename: string;
  file_size_bytes: number;
  page_count: number | null;
  mime_type: string | null;
  ocr_status: OcrStatus;
  ocr_provider_used: string | null;
  ocr_error: string | null;
  ingest_channel: IngestChannel;
  parse_status: ParseStatus;
  routing_status: RoutingStatus;
  uploaded_at: string;
}

export interface InboxList {
  items: InboxItem[];
  total: number;
}

export interface UploadResponse {
  inbox_id: string;
  ocr_status: OcrStatus;
  file_hash: string;
  file_size_bytes: number;
}

export interface OcrTextResponse {
  inbox_id: string;
  ocr_status: OcrStatus;
  ocr_text: string | null;
  ocr_provider_used: string | null;
  page_count: number | null;
  ocr_error: string | null;
}

export const INGEST_CHANNEL_LABELS: Record<IngestChannel, string> = {
  web_upload: "Upload",
  mobile_capture: "Mobile",
  email: "Email",
  gst_portal_gsp: "GST portal",
  it_portal_aa: "IT portal",
  whatsapp: "WhatsApp",
};

export const OCR_STATUS_LABELS: Record<OcrStatus, string> = {
  pending: "Uploading",
  in_progress: "OCR in progress",
  completed: "Ready for review",
  failed: "OCR failed",
};
