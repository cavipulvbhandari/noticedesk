// Server-side helper that forwards a browser request to the FastAPI with
// the dev-session cookie translated into X-Dev-* headers. Once Clerk is
// wired in, this file goes away — client components will hold a Clerk JWT
// and hit the API directly.

import { NextResponse } from "next/server";

import { readDevSession } from "@/lib/session";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function proxyToApi(
  request: Request,
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const session = readDevSession();
  if (!session) {
    return NextResponse.json(
      { error: { code: "unauthorized", message: "no session" } },
      { status: 401 },
    );
  }
  const url = new URL(request.url);
  const target = new URL(`${API_BASE}${path}`);
  url.searchParams.forEach((v, k) => target.searchParams.set(k, v));

  const headers = new Headers(init.headers);
  headers.set("X-Dev-User-Id", session.user_id);
  headers.set("X-Dev-Tenant-Id", session.tenant_id);

  const upstream = await fetch(target.toString(), {
    method: init.method ?? request.method,
    headers,
    body: init.body ?? (request.method === "GET" || request.method === "HEAD" ? undefined : request.body),
    // @ts-expect-error duplex required when body is a stream in Node 18+
    duplex: "half",
  });
  const contentType = upstream.headers.get("content-type") ?? "application/json";
  const body = await upstream.arrayBuffer();
  return new NextResponse(body, {
    status: upstream.status,
    headers: { "content-type": contentType },
  });
}
