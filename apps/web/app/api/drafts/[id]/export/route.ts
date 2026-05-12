// Proxies the .docx export. We pass through the upstream content-type and
// disposition headers so the browser triggers a native file download.

import { proxyToApi } from "@/lib/proxy";

interface Ctx {
  params: { id: string };
}

export async function GET(req: Request, { params }: Ctx) {
  const url = new URL(req.url);
  const mode = url.searchParams.get("mode") ?? "filing";
  return proxyToApi(req, `/v1/drafts/${params.id}/export?mode=${encodeURIComponent(mode)}`);
}
