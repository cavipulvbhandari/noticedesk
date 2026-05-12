import { proxyToApi } from "@/lib/proxy";

interface Ctx {
  params: { id: string };
}

export async function PATCH(req: Request, { params }: Ctx) {
  return proxyToApi(req, `/v1/documents/${params.id}`);
}
