import { proxyToApi } from "@/lib/proxy";

export async function GET(req: Request) {
  return proxyToApi(req, "/v1/notices");
}
