/**
 * Sprint 1 session helpers.
 *
 * Real auth provider (Clerk) is wired in once the India-region availability
 * decision lands. Until then, the dev-login route stores user_id + tenant_id
 * in an httpOnly cookie and the dashboard reads it through to the API as
 * X-Dev-* headers. Production environments REJECT this cookie path; the API
 * will return 401 unless ENVIRONMENT=development.
 */

import { cookies } from "next/headers";

export const DEV_SESSION_COOKIE = "noticedesk_dev_session";

export interface DevSession {
  user_id: string;
  tenant_id: string;
}

export function readDevSession(): DevSession | null {
  const raw = cookies().get(DEV_SESSION_COOKIE)?.value;
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as DevSession;
    if (!parsed.user_id || !parsed.tenant_id) return null;
    return parsed;
  } catch {
    return null;
  }
}
