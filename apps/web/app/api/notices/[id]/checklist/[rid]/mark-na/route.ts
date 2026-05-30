import { proxyToApi } from "@/lib/proxy";

interface Ctx {
  params: { id: string; rid: string };
}

export async function POST(req: Request, { params }: Ctx) {
  return proxyToApi(
    req,
    `/v1/notices/${params.id}/checklist/${params.rid}/mark-na`,
  );
}
