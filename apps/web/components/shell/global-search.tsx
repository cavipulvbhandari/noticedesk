"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { search, type SearchResult } from "@/lib/api";
import { cn } from "@/lib/cn";
import { lifecycleChipClass, lifecycleLabel } from "@/lib/lifecycle";

const DEBOUNCE_MS = 200;

export function GlobalSearch() {
  const router = useRouter();
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const [result, setResult] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  useEffect(() => {
    if (q.trim().length < 2) {
      setResult(null);
      return;
    }
    setLoading(true);
    const t = setTimeout(async () => {
      try {
        const r = await search(q.trim());
        setResult(r);
      } catch {
        setResult(null);
      } finally {
        setLoading(false);
      }
    }, DEBOUNCE_MS);
    return () => clearTimeout(t);
  }, [q]);

  function goto(href: string) {
    setOpen(false);
    setQ("");
    setResult(null);
    router.push(href);
  }

  return (
    <div ref={ref} className="relative w-full max-w-[480px]">
      <svg
        className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate opacity-60"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
      >
        <circle cx="11" cy="11" r="7" />
        <line x1="20" y1="20" x2="16.65" y2="16.65" />
      </svg>
      <input
        type="text"
        value={q}
        placeholder="Search clients (name, PAN) or notices…"
        onChange={(e) => {
          setQ(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        className="w-full rounded-sm border border-slate-line bg-white py-2 pl-9 pr-3.5 text-[13px] outline-none transition-colors focus:border-gold"
      />

      {open && q.trim().length >= 2 ? (
        <div className="absolute left-0 right-0 top-full z-40 mt-1 max-h-[420px] overflow-y-auto rounded-md border border-slate-line bg-white shadow-card-lg">
          {loading && !result ? (
            <p className="px-4 py-3 text-[12px] italic text-slate">Searching…</p>
          ) : !result || (result.clients.length === 0 && result.notices.length === 0) ? (
            <p className="px-4 py-3 text-[12px] italic text-slate">
              Nothing matches &ldquo;{q}&rdquo;.
            </p>
          ) : (
            <>
              {result.clients.length > 0 ? (
                <section>
                  <p className="border-b border-slate-line bg-paper px-4 py-1.5 text-[10px] font-semibold uppercase tracking-[0.06em] text-slate">
                    Clients
                  </p>
                  <ul>
                    {result.clients.map((c) => (
                      <li key={c.client_id}>
                        <button
                          type="button"
                          onClick={() => goto(`/clients/${c.client_id}`)}
                          className="block w-full px-4 py-2 text-left hover:bg-paper"
                        >
                          <p className="text-[13px] font-semibold text-ink">
                            {c.legal_name}
                          </p>
                          <p className="font-mono text-[11px] text-slate">
                            {c.pan} · {c.entity_type ?? "—"}
                          </p>
                        </button>
                      </li>
                    ))}
                  </ul>
                </section>
              ) : null}

              {result.notices.length > 0 ? (
                <section>
                  <p className="border-b border-slate-line bg-paper px-4 py-1.5 text-[10px] font-semibold uppercase tracking-[0.06em] text-slate">
                    Notices
                  </p>
                  <ul>
                    {result.notices.map((n) => (
                      <li key={n.notice_id}>
                        <button
                          type="button"
                          onClick={() => goto(`/matters/${n.notice_id}`)}
                          className="block w-full px-4 py-2 text-left hover:bg-paper"
                        >
                          <div className="flex items-center justify-between gap-2">
                            <p className="truncate text-[13px] text-ink">
                              {n.issue ?? n.document_type ?? "—"}
                            </p>
                            <span
                              className={cn(
                                "shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide",
                                lifecycleChipClass(n.lifecycle_status),
                              )}
                            >
                              {lifecycleLabel(n.lifecycle_status)}
                            </span>
                          </div>
                          <p className="mt-0.5 text-[11px] text-slate">
                            {n.client_legal_name}
                            {n.document_type ? ` · ${n.document_type}` : ""}
                            {n.due_date ? ` · due ${n.due_date}` : ""}
                          </p>
                        </button>
                      </li>
                    ))}
                  </ul>
                </section>
              ) : null}
            </>
          )}
        </div>
      ) : null}
    </div>
  );
}
