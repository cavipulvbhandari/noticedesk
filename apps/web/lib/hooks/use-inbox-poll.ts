"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { fetchInbox, type InboxList } from "@/lib/api";

const POLL_INTERVAL_MS = 3000;
const ACTIVE_OCR: ReadonlySet<string> = new Set(["pending", "in_progress"]);
const ACTIVE_PARSE: ReadonlySet<string> = new Set(["pending", "in_progress"]);

export interface UseInboxPollResult {
  data: InboxList | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export function useInboxPoll(): UseInboxPollResult {
  const [data, setData] = useState<InboxList | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const cancelled = useRef(false);

  const tick = useCallback(async () => {
    try {
      const next = await fetchInbox();
      if (cancelled.current) return;
      setData(next);
      setError(null);
      const hasActive = next.items.some(
        (i) =>
          ACTIVE_OCR.has(i.ocr_status) ||
          (i.ocr_status === "completed" && ACTIVE_PARSE.has(i.parse_status)),
      );
      if (hasActive) {
        timer.current = setTimeout(tick, POLL_INTERVAL_MS);
      }
    } catch (e: unknown) {
      if (cancelled.current) return;
      setError(e instanceof Error ? e.message : "failed to load inbox");
      // Back off but keep trying.
      timer.current = setTimeout(tick, POLL_INTERVAL_MS * 2);
    } finally {
      if (!cancelled.current) setLoading(false);
    }
  }, []);

  const refresh = useCallback(async () => {
    if (timer.current) clearTimeout(timer.current);
    setLoading(true);
    await tick();
  }, [tick]);

  useEffect(() => {
    cancelled.current = false;
    void tick();
    return () => {
      cancelled.current = true;
      if (timer.current) clearTimeout(timer.current);
    };
  }, [tick]);

  return { data, loading, error, refresh };
}
