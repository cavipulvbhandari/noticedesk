import { NextResponse } from "next/server";

import { DEV_SESSION_COOKIE } from "@/lib/session";

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export async function POST(req: Request) {
  const body = await req.json().catch(() => null);
  if (!body || typeof body !== "object") {
    return NextResponse.json(
      { error: { code: "validation_error", message: "invalid body" } },
      { status: 400 },
    );
  }

  const { user_id, tenant_id } = body as { user_id?: string; tenant_id?: string };
  if (!user_id || !tenant_id || !UUID_RE.test(user_id) || !UUID_RE.test(tenant_id)) {
    return NextResponse.json(
      { error: { code: "validation_error", message: "user_id and tenant_id must be UUIDs" } },
      { status: 400 },
    );
  }

  const res = NextResponse.json({ ok: true });
  res.cookies.set({
    name: DEV_SESSION_COOKIE,
    value: JSON.stringify({ user_id, tenant_id }),
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 60 * 60 * 8,
  });
  return res;
}
