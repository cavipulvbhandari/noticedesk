// Two backend handlers funnel through this single dynamic route to avoid a
// Next.js slug-name collision:
// - POST  /v1/clients/{id}/registrations    (creates a registration for a client)
// - PATCH /v1/registrations/{id}            (updates an existing registration)
//
// They look like different REST resources but live at the same Next.js path
// segment because both take a UUID. The path identity is decided by the HTTP
// method on the wrapper, not by the URL alone.

import { proxyToApi } from "@/lib/proxy";

interface Ctx {
  params: { id: string };
}

export async function POST(req: Request, { params }: Ctx) {
  return proxyToApi(req, `/v1/clients/${params.id}/registrations`);
}

export async function PATCH(req: Request, { params }: Ctx) {
  return proxyToApi(req, `/v1/registrations/${params.id}`);
}
