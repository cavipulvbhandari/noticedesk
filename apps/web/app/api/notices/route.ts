// /v1/notices is a list (GET) + create (POST); /v1/notices/{id} is detail
// (GET) + update (PATCH). Both Next routes proxy method-by-method.

import { proxyToApi } from "@/lib/proxy";

export async function GET(req: Request) {
  return proxyToApi(req, "/v1/notices");
}

export async function POST(req: Request) {
  return proxyToApi(req, "/v1/notices");
}
