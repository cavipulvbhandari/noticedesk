import { Search } from "lucide-react";

interface TopbarProps {
  userName: string | null;
  tenantName: string | null;
  role: string | null;
}

function initialsFor(name: string | null): string {
  if (!name) return "··";
  const parts = name.trim().split(/\s+/).filter(Boolean);
  const first = parts[0];
  const last = parts[parts.length - 1];
  if (!first) return "··";
  if (parts.length === 1 || !last) return first.slice(0, 2).toUpperCase();
  return ((first[0] ?? "") + (last[0] ?? "")).toUpperCase();
}

export function Topbar({ userName, tenantName, role }: TopbarProps): React.ReactElement {
  return (
    <header className="flex h-14 items-center gap-4 border-b border-slate/15 bg-paper px-6">
      <div className="relative w-full max-w-md">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate" />
        <input
          type="search"
          placeholder="Search clients, notices, PAN…"
          aria-label="Search"
          disabled
          className="w-full rounded-md border border-slate/20 bg-cream py-2 pl-9 pr-3 text-sm text-ink placeholder:text-slate focus:border-gold focus:outline-none"
        />
      </div>
      <div className="ml-auto flex items-center gap-3">
        <div className="hidden text-right sm:block">
          <div className="text-sm font-medium text-ink">{userName ?? "—"}</div>
          <div className="text-[11px] uppercase tracking-wider text-slate">
            {role ?? "—"} · {tenantName ?? "—"}
          </div>
        </div>
        <div className="grid h-9 w-9 place-items-center rounded-full bg-navy text-cream font-medium">
          {initialsFor(userName)}
        </div>
      </div>
    </header>
  );
}
