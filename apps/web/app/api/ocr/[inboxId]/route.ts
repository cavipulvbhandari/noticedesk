import { proxyToApi } from "@/lib/proxy";

export async function GET(
  req: Request,
  { params }: { params: { inboxId: string } },
) {
  return proxyToApi(req, `/v1/documents/inbox/${params.inboxId}/ocr`);
}
