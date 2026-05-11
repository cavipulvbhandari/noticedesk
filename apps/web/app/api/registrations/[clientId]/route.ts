import { proxyToApi } from "@/lib/proxy";

export async function POST(
  req: Request,
  { params }: { params: { clientId: string } },
) {
  return proxyToApi(req, `/v1/clients/${params.clientId}/registrations`);
}
