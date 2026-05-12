import { proxyToApi } from "@/lib/proxy";

interface Ctx {
  params: { id: string };
}

export async function GET(req: Request, { params }: Ctx) {
  return proxyToApi(req, `/v1/matters/${params.id}/documents`);
}

export async function POST(req: Request, { params }: Ctx) {
  const url = new URL(req.url);
  const docType = url.searchParams.get("document_type") ?? "supporting";
  return proxyToApi(
    req,
    `/v1/matters/${params.id}/documents?document_type=${encodeURIComponent(docType)}`,
  );
}
