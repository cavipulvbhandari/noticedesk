import Link from "next/link";
import { Calendar, Inbox, LayoutDashboard, Upload, Users } from "lucide-react";

const links = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/inbox", label: "Inbox", icon: Inbox },
  { href: "/clients", label: "Clients", icon: Users },
  { href: "/calendar", label: "Calendar", icon: Calendar },
];

export function Sidebar() {
  return (
    <aside className="hidden w-56 shrink-0 border-r border-slate-200 bg-white px-4 py-6 md:block">
      <Link href="/" className="mb-8 block text-lg font-semibold text-navy">
        NoticeDesk
      </Link>
      <nav className="space-y-1">
        {links.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className="flex items-center gap-2 rounded px-2 py-1.5 text-sm text-slate-700 hover:bg-slate-100"
          >
            <Icon className="h-4 w-4" aria-hidden /> {label}
          </Link>
        ))}
      </nav>
      <div className="mt-8 border-t border-slate-200 pt-4">
        <Link
          href="/inbox?upload=1"
          className="flex items-center gap-2 rounded bg-navy px-3 py-2 text-sm font-medium text-white hover:bg-navy-500"
        >
          <Upload className="h-4 w-4" aria-hidden /> Upload notice
        </Link>
      </div>
    </aside>
  );
}
