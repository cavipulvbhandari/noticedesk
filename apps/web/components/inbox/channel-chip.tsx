import { INGEST_CHANNEL_LABELS, type IngestChannel } from "@noticedesk/shared/inbox";
import {
  ArrowUpFromLine,
  Keyboard,
  Mail,
  Phone,
  RefreshCcw,
  Smartphone,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";

const ICONS: Record<IngestChannel, typeof Mail> = {
  web_upload: ArrowUpFromLine,
  mobile_capture: Smartphone,
  email: Mail,
  gst_portal_gsp: RefreshCcw,
  it_portal_aa: RefreshCcw,
  whatsapp: Phone,
};

export function ChannelChip({ channel }: { channel: IngestChannel }) {
  const Icon = ICONS[channel] ?? Keyboard;
  return (
    <Badge tone="navy">
      <Icon className="h-3.5 w-3.5" aria-hidden />
      {INGEST_CHANNEL_LABELS[channel]}
    </Badge>
  );
}
