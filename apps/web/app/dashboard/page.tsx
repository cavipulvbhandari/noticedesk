import { redirect } from "next/navigation";

import { AppShell } from "@/components/shell/AppShell";
import { readDevSession } from "@/lib/session";

interface SessionResponse {
  user: {
    user_id: string;
    name: string;
    role: string;
    email: string | null;
    mfa_enabled?: boolean;
  };
  tenant: { tenant_id: string; legal_name: string };
}

async function fetchMe(userId: string, tenantId: string): Promise<SessionResponse | null> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  try {
    const res = await fetch(`${baseUrl}/v1/me`, {
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

function timeAwareGreeting(now: Date = new Date()): string {
  // Asia/Kolkata is the only locale we serve; render the IST hour regardless
  // of the server's clock zone so SSR and client agree.
  const istHour = Number(
    new Intl.DateTimeFormat("en-IN", {
      hour: "numeric",
      hour12: false,
      timeZone: "Asia/Kolkata",
    }).format(now),
  );
  if (istHour < 12) return "Good morning";
  if (istHour < 17) return "Good afternoon";
  return "Good evening";
}

function firstName(fullName: string | undefined | null): string {
  if (!fullName) return "";
  const trimmed = fullName.trim();
  if (!trimmed) return "";
  // CA Rohan Mehta → "Rohan"; "Anjali Kapoor" → "Anjali".
  const parts = trimmed.split(/\s+/);
  if (parts[0] === "CA" && parts.length > 1) return parts[1] ?? "";
  return parts[0] ?? "";
}

function formatToday(now: Date = new Date()): string {
  return new Intl.DateTimeFormat("en-IN", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "Asia/Kolkata",
  }).format(now);
}

export default async function DashboardPage(): Promise<React.ReactElement> {
  const session = readDevSession();
  if (!session) {
    redirect("/login");
  }

  const data = await fetchMe(session.user_id, session.tenant_id);
  const greeting = timeAwareGreeting();
  const today = formatToday();

  return (
    <AppShell
      userName={data?.user.name ?? null}
      tenantName={data?.tenant.legal_name ?? null}
      role={data?.user.role ?? null}
    >
      <header className="mb-10">
        <p className="text-[11px] uppercase tracking-[0.2em] text-slate">
          {today}
        </p>
        <h1 className="mt-2 font-serif text-4xl text-navy">
          {greeting}
          {data ? `, ${firstName(data.user.name)}` : ""}.
        </h1>
        <p className="mt-2 text-sm text-slate">
          {data
            ? `Signed in to ${data.tenant.legal_name} as ${data.user.role}.`
            : "Could not load session — check the API is running and the user/tenant IDs exist."}
        </p>
      </header>

      <section className="rounded-lg border border-slate/15 bg-paper p-6 shadow-sm">
        <h2 className="font-serif text-xl text-navy">Sprint 1 — Foundation</h2>
        <p className="mt-2 text-sm text-slate">
          The PAN-centric data model, RLS, identity utility, auth scaffold,
          and UI shell are in place. Notice ingest, OCR, parsing, routing,
          drafting, and the matter dashboards begin in Sprint 2.
        </p>
        <ul className="mt-4 grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
          <li className="rounded-md border border-slate/10 bg-cream px-3 py-2">
            <span className="text-[10px] uppercase tracking-wider text-slate">
              Identity
            </span>
            <div className="mt-0.5 font-mono text-ink">PAN-keyed clients</div>
          </li>
          <li className="rounded-md border border-slate/10 bg-cream px-3 py-2">
            <span className="text-[10px] uppercase tracking-wider text-slate">
              Tenancy
            </span>
            <div className="mt-0.5 font-mono text-ink">Row-level security</div>
          </li>
          <li className="rounded-md border border-slate/10 bg-cream px-3 py-2">
            <span className="text-[10px] uppercase tracking-wider text-slate">
              Audit
            </span>
            <div className="mt-0.5 font-mono text-ink">Append-only log</div>
          </li>
          <li className="rounded-md border border-slate/10 bg-cream px-3 py-2">
            <span className="text-[10px] uppercase tracking-wider text-slate">
              Region
            </span>
            <div className="mt-0.5 font-mono text-ink">AWS Mumbai · DPDP</div>
          </li>
        </ul>
      </section>
    </AppShell>
  );
}
