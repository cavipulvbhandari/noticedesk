import { proxyToApi } from "@/lib/proxy";

export async function POST(
  req: Request,
  { params }: { params: { inboxId: string } },
) {
  return proxyToApi(req, `/v1/inbox/${params.inboxId}/route_manually`);
}
