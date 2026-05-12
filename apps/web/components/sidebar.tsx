"use client";

import { Calendar, Inbox, LayoutDashboard, Settings, Upload, Users } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/cn";

const links = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard, key: "dashboard" as const },
  { href: "/inbox", label: "Inbox", icon: Inbox, key: "inbox" as const },
  { href: "/clients", label: "Clients", icon: Users, key: "clients" as const },
  { href: "/calendar", label: "Calendar", icon: Calendar, key: "calendar" as const },
  { href: "/settings", label: "Settings", icon: Settings, key: "settings" as const },
];

interface Props {
  inboxAwaiting?: number;
}

export function Sidebar({ inboxAwaiting = 0 }: Props) {
  const pathname = usePathname() ?? "";
  return (
    <aside className="hidden w-[240px] shrink-0 flex-col border-r border-navy-rail/30 bg-navy-rail py-5 text-paper md:flex">
      <Link
        href="/dashboard"
        className="mb-7 flex items-center gap-2 px-6 font-serif text-[22px] font-semibold tracking-tight text-paper"
      >
        Notice<span className="text-gold">Desk</span>
        <span className="ml-auto rounded-sm bg-gold/15 px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-[0.18em] text-gold-soft">
          Phase 1
        </span>
      </Link>

      <nav className="flex-1 space-y-px px-3">
        {links.map(({ href, label, icon: Icon, key }) => {
          const isActive = pathname === href || pathname.startsWith(`${href}/`);
          const badge = key === "inbox" && inboxAwaiting > 0 ? inboxAwaiting : null;
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "relative flex items-center gap-3 rounded-sm px-3 py-2 text-[13.5px] font-medium transition-colors",
                isActive
                  ? "bg-gold/15 text-paper"
                  : "text-paper/75 hover:bg-gold/10 hover:text-paper",
              )}
            >
              {isActive ? (
                <span className="absolute -left-3 top-2 bottom-2 w-[3px] rounded-r-sm bg-gold" />
              ) : null}
              <Icon className="h-4 w-4 opacity-85" aria-hidden />
              {label}
              {badge !== null ? (
                <span className="ml-auto rounded-full bg-gold px-1.5 py-0.5 text-[10px] font-bold leading-none text-navy-deep">
                  {badge}
                </span>
              ) : null}
            </Link>
          );
        })}
      </nav>

      <div className="mt-6 px-3">
        <Link
          href="/inbox?upload=1"
          className="flex items-center gap-2 rounded-sm bg-gold px-3 py-2 text-[13px] font-semibold text-navy-deep transition-colors hover:bg-gold-soft"
        >
          <Upload className="h-4 w-4" aria-hidden /> Upload notice
        </Link>
      </div>

      <div className="mt-auto border-t border-gold/15 px-6 pt-4 text-[11px] text-paper/60">
        <p className="font-serif text-[13px] font-semibold text-paper">Mehta &amp; Associates</p>
        <p className="mt-0.5">Mumbai · 4 partners</p>
      </div>
    </aside>
  );
}
