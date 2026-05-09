"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Route } from "next";
import {
  LayoutDashboard,
  Inbox,
  CalendarDays,
  Users,
  Upload,
  Settings,
  type LucideIcon,
} from "lucide-react";

import { cn } from "@/lib/cn";

interface NavItem {
  href: Route;
  label: string;
  icon: LucideIcon;
  badge?: number;
}

// Sprint 1 ships the rail; later sprints wire up the destinations.
const NAV: NavItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/inbox", label: "Inbox", icon: Inbox, badge: 0 },
  { href: "/calendar", label: "Calendar", icon: CalendarDays },
  { href: "/clients", label: "Clients", icon: Users },
  { href: "/upload", label: "Upload notice", icon: Upload },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar(): React.ReactElement {
  const pathname = usePathname();

  return (
    <aside className="hidden md:flex w-60 shrink-0 flex-col border-r border-slate/15 bg-paper">
      <div className="px-5 py-6">
        <div className="font-serif text-xl tracking-tight text-navy">
          NoticeDesk
        </div>
        <div className="mt-0.5 text-[11px] uppercase tracking-[0.18em] text-slate">
          Litigation OS
        </div>
      </div>
      <nav className="flex-1 px-3 pb-6">
        <ul className="space-y-0.5">
          {NAV.map((item) => {
            const active =
              pathname === item.href ||
              (item.href !== "/dashboard" && pathname?.startsWith(item.href));
            const Icon = item.icon;
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                    active
                      ? "bg-navy text-cream"
                      : "text-ink hover:bg-cream",
                  )}
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  <span className="flex-1">{item.label}</span>
                  {typeof item.badge === "number" && item.badge > 0 ? (
                    <span className="rounded-full bg-gold px-2 py-0.5 text-[10px] font-medium text-cream">
                      {item.badge}
                    </span>
                  ) : null}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
      <div className="px-5 py-4 text-[11px] text-slate">
        Phase 1 · Sprint 1
      </div>
    </aside>
  );
}
