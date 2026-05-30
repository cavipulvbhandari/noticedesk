import { proxyToApi } from "@/lib/proxy";

interface Ctx {
  params: { id: string };
}

export async function POST(req: Request, { params }: Ctx) {
  return proxyToApi(req, `/v1/notices/${params.id}/triage`);
}

export async function GET(req: Request, { params }: Ctx) {
  return proxyToApi(req, `/v1/notices/${params.id}/triage`);
}
