"use client";

import { useRouter } from "next/navigation";

import type { NoticeListRow } from "@/lib/api";
import { cn } from "@/lib/cn";

interface Props {
  year: number;
  month: number; // 1-12
  notices: NoticeListRow[];
  today: Date;
}

interface Cell {
  day: number;
  month: number;
  year: number;
  other: boolean;
}

// Build a Monday-first calendar for the given month. We pad the front with
// trailing days of the previous month and the back with leading days of the
// next month so the grid is always a clean 5-or-6 row block.
function buildMonth(year: number, month: number): Cell[] {
  const first = new Date(Date.UTC(year, month - 1, 1));
  // JS getUTCDay(): 0=Sun..6=Sat. We want Mon=0.
  const firstDow = (first.getUTCDay() + 6) % 7;
  const daysInMonth = new Date(Date.UTC(year, month, 0)).getUTCDate();
  const prevMonthDays = new Date(Date.UTC(year, month - 1, 0)).getUTCDate();

  const cells: Cell[] = [];
  for (let i = firstDow; i > 0; i--) {
    cells.push({
      day: prevMonthDays - i + 1,
      month: month - 1 > 0 ? month - 1 : 12,
      year: month - 1 > 0 ? year : year - 1,
      other: true,
    });
  }
  for (let d = 1; d <= daysInMonth; d++) {
    cells.push({ day: d, month, year, other: false });
  }
  while (cells.length % 7 !== 0) {
    const next = cells[cells.length - 1]!;
    const day = next.other ? next.day + 1 : 1;
    cells.push({
      day: cells[cells.length - 1]!.other ? day : (cells[cells.length - 1]!.day === daysInMonth ? 1 : day),
      month: month + 1 > 12 ? 1 : month + 1,
      year: month + 1 > 12 ? year + 1 : year,
      other: true,
    });
  }
  // Ensure 6 rows for visual stability when months are short.
  while (cells.length < 42) {
    const last = cells[cells.length - 1]!;
    cells.push({
      day: last.day + 1,
      month: last.month,
      year: last.year,
      other: true,
    });
  }
  return cells;
}

function dayClassFor(dueIso: string, today: Date): string {
  const due = new Date(dueIso);
  due.setHours(0, 0, 0, 0);
  const t = new Date(today);
  t.setHours(0, 0, 0, 0);
  const diff = Math.round((due.getTime() - t.getTime()) / (1000 * 60 * 60 * 24));
  if (diff < 0)
    return "bg-alarm-bg text-alarm border-l-2 border-alarm";
  if (diff <= 7)
    return "bg-warn-bg text-[#8B5C1F] border-l-2 border-warn";
  return "bg-paper-warm text-ink-soft border-l-2 border-gold";
}

const DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export function CalendarGrid({ year, month, notices, today }: Props) {
  const router = useRouter();
  const cells = buildMonth(year, month);

  // Bucket notices by ISO YYYY-MM-DD for O(1) lookup per cell.
  const byDay = new Map<string, NoticeListRow[]>();
  for (const n of notices) {
    if (!n.due_date) continue;
    const list = byDay.get(n.due_date) ?? [];
    list.push(n);
    byDay.set(n.due_date, list);
  }

  return (
    <div className="overflow-hidden rounded-md border border-slate-line bg-white">
      <div className="grid grid-cols-7 border-b border-slate-line bg-paper">
        {DOW.map((d) => (
          <div
            key={d}
            className="px-3 py-2 text-[10.5px] font-semibold uppercase tracking-[0.06em] text-slate"
          >
            {d}
          </div>
        ))}
      </div>
      <div className="grid grid-cols-7 gap-px bg-slate-line">
        {cells.map((cell, idx) => {
          const iso = `${cell.year}-${String(cell.month).padStart(2, "0")}-${String(cell.day).padStart(2, "0")}`;
          const events = byDay.get(iso) ?? [];
          const isToday =
            cell.year === today.getFullYear() &&
            cell.month === today.getMonth() + 1 &&
            cell.day === today.getDate() &&
            !cell.other;
          return (
            <div
              key={idx}
              className={cn(
                "min-h-[110px] bg-white p-2",
                cell.other && "bg-paper text-slate",
                isToday && "ring-2 ring-inset ring-gold",
              )}
            >
              <div
                className={cn(
                  "mb-1 text-[12px] font-semibold",
                  isToday ? "text-gold-dark" : cell.other ? "text-slate-pale" : "text-ink",
                )}
              >
                {cell.day}
              </div>
              {events.slice(0, 3).map((e) => (
                <button
                  key={e.notice_id}
                  type="button"
                  onClick={() => router.push(`/matters/${e.notice_id}`)}
                  title={`${e.client_legal_name} · ${e.document_type ?? e.law}`}
                  className={cn(
                    "mb-1 w-full truncate rounded-sm px-1.5 py-0.5 text-left text-[10.5px] font-medium",
                    dayClassFor(e.due_date!, today),
                  )}
                >
                  {(e.client_legal_name.split(" ")[0] ?? "—")} · {e.document_type ?? e.law}
                </button>
              ))}
              {events.length > 3 ? (
                <p className="text-[9px] font-semibold text-slate">
                  +{events.length - 3} more
                </p>
              ) : null}
            </div>
          );
        })}
      </div>
    </div>
  );
}
