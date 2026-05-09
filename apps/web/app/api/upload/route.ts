import { proxyToApi } from "@/lib/proxy";

export async function POST(req: Request) {
  return proxyToApi(req, "/v1/documents/upload");
}
