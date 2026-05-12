"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { CalendarGrid } from "@/components/calendar/calendar-grid";
import { Button } from "@/components/ui/button";
import { fetchNotices, type NoticeListRow } from "@/lib/api";

const MONTHS = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

export default function CalendarPage() {
  const today = useMemo(() => new Date(), []);
  const [year, setYear] = useState<number>(today.getFullYear());
  const [month, setMonth] = useState<number>(today.getMonth() + 1); // 1-12
  const [notices, setNotices] = useState<NoticeListRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    (async () => {
      try {
        // Fetch the whole visible window (one month padded by neighbours).
        // The grid pads by ~6 days on each side worst case; widen the
        // window to be safe — backend filters by due_date inclusive.
        const from = `${year}-${String(month).padStart(2, "0")}-01`;
        const lastDay = new Date(year, month, 0).getDate();
        const to = `${year}-${String(month).padStart(2, "0")}-${lastDay}`;
        const widenedFrom = shift(from, -7);
        const widenedTo = shift(to, 7);
        const res = await fetchNotices({
          from: widenedFrom,
          to: widenedTo,
          page_size: 200,
        });
        if (!cancelled) setNotices(res.notices);
      } catch (e: unknown) {
        if (!cancelled) setError(e instanceof Error ? e.message : "failed to load");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [year, month]);

  const dueThisMonth = notices.filter((n) => {
    if (!n.due_date) return false;
    const d = new Date(n.due_date);
    return (
      d.getFullYear() === year &&
      d.getMonth() + 1 === month &&
      ["issued", "in_progress", "due", "due_date_over"].includes(n.lifecycle_status)
    );
  });
  const overdueAll = notices.filter((n) => n.lifecycle_status === "due_date_over");

  function nudge(delta: number) {
    const next = new Date(year, month - 1 + delta, 1);
    setYear(next.getFullYear());
    setMonth(next.getMonth() + 1);
  }

  return (
    <main className="mx-auto max-w-[1400px] px-10 py-8 pb-16">
      <header className="mb-7 flex flex-wrap items-end justify-between gap-6">
        <div>
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-ink">
            Calendar
          </p>
          <h1 className="font-serif text-[36px] font-medium tracking-tight text-navy-deep">
            {MONTHS[month - 1]} {year}
          </h1>
          <p className="mt-1 font-serif text-[17px] italic text-slate">
            {dueThisMonth.length} {dueThisMonth.length === 1 ? "deadline" : "deadlines"} this
            month · {overdueAll.length} overdue
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={() => nudge(-1)} aria-label="Previous month">
            <ChevronLeft className="mr-1 h-3.5 w-3.5" aria-hidden /> {MONTHS[(month + 10) % 12]}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() =>
              (setYear(today.getFullYear()), setMonth(today.getMonth() + 1))
            }
          >
            Today
          </Button>
          <Button variant="ghost" size="sm" onClick={() => nudge(1)} aria-label="Next month">
            {MONTHS[month % 12]} <ChevronRight className="ml-1 h-3.5 w-3.5" aria-hidden />
          </Button>
        </div>
      </header>

      {error ? (
        <p className="mb-4 rounded border border-alarm/30 bg-alarm-bg px-3 py-2 text-sm text-alarm">
          {error}
        </p>
      ) : null}

      {loading ? (
        <p className="py-10 text-center font-serif italic text-slate">Loading calendar…</p>
      ) : (
        <CalendarGrid year={year} month={month} notices={notices} today={today} />
      )}

      <div className="mt-5 flex flex-wrap items-center gap-5 text-[11.5px] text-slate">
        <span className="text-[10px] font-semibold uppercase tracking-[0.06em]">Legend</span>
        <LegendSwatch swatch="bg-alarm-bg border-alarm" label="Overdue" />
        <LegendSwatch swatch="bg-warn-bg border-warn" label="Due within 7 days" />
        <LegendSwatch swatch="bg-paper-warm border-gold" label="Upcoming" />
      </div>
    </main>
  );
}

function LegendSwatch({ swatch, label }: { swatch: string; label: string }) {
  return (
    <span className="flex items-center gap-1.5">
      <span className={`inline-block h-2 w-3.5 border-l-2 ${swatch}`} />
      {label}
    </span>
  );
}

function shift(iso: string, days: number): string {
  const d = new Date(iso);
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}
