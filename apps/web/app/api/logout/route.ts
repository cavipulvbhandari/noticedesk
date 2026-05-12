// Clears the dev-session cookie and redirects back to /login.
// Sprint 2 will swap this for a Clerk session.signOut() call.

import { NextResponse } from "next/server";

import { DEV_SESSION_COOKIE } from "@/lib/session";

export async function POST() {
  const res = NextResponse.json({ ok: true });
  res.cookies.set({
    name: DEV_SESSION_COOKIE,
    value: "",
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: 0,
  });
  return res;
}
