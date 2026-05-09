import { OCR_STATUS_LABELS, type OcrStatus } from "@noticedesk/shared/inbox";
import { CheckCircle2, CircleAlert, Clock, Loader2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";

const TONE: Record<OcrStatus, "neutral" | "warning" | "success" | "danger"> = {
  pending: "neutral",
  in_progress: "warning",
  completed: "success",
  failed: "danger",
};

export function OcrStatusChip({ status }: { status: OcrStatus }) {
  const Icon =
    status === "completed"
      ? CheckCircle2
      : status === "failed"
        ? CircleAlert
        : status === "in_progress"
          ? Loader2
          : Clock;
  return (
    <Badge tone={TONE[status]}>
      <Icon
        className={
          status === "in_progress"
            ? "h-3.5 w-3.5 animate-spin"
            : "h-3.5 w-3.5"
        }
        aria-hidden
      />
      {OCR_STATUS_LABELS[status]}
    </Badge>
  );
}
