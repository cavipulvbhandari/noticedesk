import { redirect } from "next/navigation";

import { readDevSession } from "@/lib/session";

interface SessionResponse {
  user: { user_id: string; name: string; role: string; email: string | null };
  tenant: { tenant_id: string; legal_name: string };
}

async function fetchSession(userId: string, tenantId: string): Promise<SessionResponse | null> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  try {
    const res = await fetch(`${baseUrl}/v1/session`, {
      headers: {
        "X-Dev-User-Id": userId,
        "X-Dev-Tenant-Id": tenantId,
      },
      cache: "no-store",
    });
    if (!res.ok) return null;
    return (await res.json()) as SessionResponse;
  } catch {
    return null;
  }
}

export default async function DashboardPage() {
  const session = readDevSession();
  if (!session) {
    redirect("/login");
  }

  const data = await fetchSession(session.user_id, session.tenant_id);

  return (
    <main className="mx-auto max-w-4xl px-6 py-12">
      <header className="mb-8">
        <p className="text-sm uppercase tracking-wider text-slate-500">Dashboard</p>
        <h1 className="mt-1 text-3xl font-semibold text-navy">
          {data ? `Welcome, ${data.user.name}` : "Welcome"}
        </h1>
        <p className="mt-1 text-slate-600">
          {data
            ? `You are signed in to ${data.tenant.legal_name} as ${data.user.role}.`
            : "Could not load session — check the API is running and the user/tenant IDs exist."}
        </p>
      </header>

      <section className="rounded-lg border border-slate-200 bg-white p-6">
        <h2 className="text-lg font-medium text-navy">Sprint 1 — Foundation</h2>
        <p className="mt-2 text-sm text-slate-600">
          The data model, RLS, identity utility, and auth scaffold are in
          place. Notice ingest, drafting, reminders, WhatsApp, and the matter
          dashboard begin in Sprint 2.
        </p>
      </section>
    </main>
  );
}
