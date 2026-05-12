"use client";

import { Bell, LogOut } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { GlobalSearch } from "@/components/shell/global-search";
import { useToast } from "@/components/ui/toast";
import { logout } from "@/lib/api";
import { cn } from "@/lib/cn";

interface Props {
  awaitingCount: number;
}

export function Topbar({ awaitingCount }: Props) {
  const router = useRouter();
  const { toast } = useToast();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!menuOpen) return;
    const onDoc = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [menuOpen]);

  async function handleSignOut() {
    await logout();
    router.push("/login");
  }

  return (
    <div className="flex h-16 items-center gap-6 border-b border-slate-line bg-paper px-8">
      <GlobalSearch />
      <div className="ml-auto flex items-center gap-3">
        <button
          type="button"
          className="relative flex h-9 w-9 items-center justify-center rounded-sm text-slate transition-colors hover:bg-paper-tint hover:text-ink"
          onClick={() =>
            toast(
              awaitingCount > 0
                ? `${awaitingCount} document${awaitingCount === 1 ? "" : "s"} awaiting in the inbox`
                : "Inbox is clear",
              "info",
            )
          }
          aria-label="Notifications"
        >
          <Bell className="h-4 w-4" aria-hidden />
          {awaitingCount > 0 ? (
            <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full border-2 border-paper bg-gold" />
          ) : null}
        </button>
        <div ref={menuRef} className="relative">
          <button
            type="button"
            onClick={() => setMenuOpen((o) => !o)}
            className="flex items-center gap-2.5 rounded-sm px-1.5 py-1 transition-colors hover:bg-paper-tint"
          >
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-navy font-serif text-[12px] font-semibold text-paper">
              RM
            </span>
            <span className="text-left text-[12px] leading-tight">
              <span className="block font-semibold text-ink">Rohan Mehta</span>
              <span className="block text-[11px] text-slate">Managing Partner</span>
            </span>
          </button>
          {menuOpen ? (
            <div className="absolute right-0 top-full z-40 mt-1 w-[200px] rounded-md border border-slate-line bg-white py-1 shadow-card-lg">
              <button
                type="button"
                onClick={() => {
                  setMenuOpen(false);
                  router.push("/settings");
                }}
                className={cn(
                  "block w-full px-3.5 py-2 text-left text-[13px] text-ink hover:bg-paper",
                )}
              >
                Settings
              </button>
              <div className="my-1 border-t border-slate-line" />
              <button
                type="button"
                onClick={handleSignOut}
                className="flex w-full items-center gap-2 px-3.5 py-2 text-left text-[13px] text-alarm hover:bg-alarm-bg"
              >
                <LogOut className="h-3.5 w-3.5" aria-hidden /> Sign out
              </button>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
