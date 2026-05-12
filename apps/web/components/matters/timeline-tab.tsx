"use client";

import { useEffect, useState } from "react";

import { fetchTimeline, type TimelineEvent } from "@/lib/api";
import { lifecycleLabel } from "@/lib/lifecycle";

interface Props {
  noticeId: string;
}

function fmtAction(e: TimelineEvent): string {
  switch (e.action_type) {
    case "notice.created":
      return "added this notice";
    case "notice.updated":
      return "updated notice fields";
    case "notice.lifecycle_changed": {
      const next =
        (e.after_state as { lifecycle_status?: string })?.lifecycle_status ?? "—";
      return `moved this to ${lifecycleLabel(next)}`;
    }
    default:
      return e.action_type;
  }
}

function fmtReason(e: TimelineEvent): string | null {
  const r = (e.after_state as { reason?: string | null })?.reason;
  return r && typeof r === "string" && r.trim() ? r : null;
}

function fmtWhen(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function TimelineTab({ noticeId }: Props) {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetchTimeline(noticeId);
        if (!cancelled) setEvents(res.events);
      } catch (e: unknown) {
        if (!cancelled) setError(e instanceof Error ? e.message : "failed to load timeline");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [noticeId]);

  if (loading) {
    return <p className="py-10 text-center font-serif italic text-slate">Loading timeline…</p>;
  }
  if (error) {
    return (
      <p className="rounded border border-alarm/30 bg-alarm-bg px-3 py-2 text-sm text-alarm">
        {error}
      </p>
    );
  }
  if (events.length === 0) {
    return (
      <div className="rounded-md border border-slate-line bg-white px-6 py-10 text-center">
        <p className="font-serif text-[15px] italic text-slate">
          No events recorded yet. Move this notice through a lifecycle state to
          start the timeline.
        </p>
      </div>
    );
  }

  return (
    <ol className="space-y-3">
      {events.map((e) => {
        const reason = fmtReason(e);
        return (
          <li
            key={e.audit_id}
            className="flex gap-4 rounded-md border border-slate-line bg-white px-5 py-4"
          >
            <div className="mt-1 h-2 w-2 shrink-0 rounded-full bg-gold" aria-hidden />
            <div className="min-w-0 flex-1">
              <p className="text-[13px] text-ink">
                <strong className="font-semibold">
                  {e.user_name ?? "Someone"}
                </strong>{" "}
                {fmtAction(e)}
              </p>
              {reason ? (
                <p className="mt-1 font-serif text-[13px] italic text-slate">{reason}</p>
              ) : null}
              <p className="mt-1 text-[11px] text-slate">
                {fmtWhen(e.timestamp)}
                {e.risk_tier ? ` · risk tier ${e.risk_tier}` : ""}
              </p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
