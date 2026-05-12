// Shared lifecycle labels + chip styling used by the dashboard, the client
// detail view, and the year-group drilldowns. Keep this in sync with the
// notices.lifecycle_status CHECK constraint in migration 0004.

export type Lifecycle =
  | "issued"
  | "in_progress"
  | "due"
  | "due_date_over"
  | "reply_submitted"
  | "acknowledged"
  | "order_received"
  | "appeal_filed"
  | "closed"
  | "on_hold";

export const LIFECYCLE_LABELS: Record<Lifecycle, string> = {
  issued: "Issued",
  in_progress: "In Progress",
  due: "Due",
  due_date_over: "Due Date Over",
  reply_submitted: "Reply Submitted",
  acknowledged: "Acknowledged",
  order_received: "Order Received",
  appeal_filed: "Appeal Filed",
  closed: "Closed",
  on_hold: "On Hold",
};

// Tailwind class string for the inline chip. Pairs with the cream/paper
// design tokens — see tailwind.config.ts.
export const LIFECYCLE_CHIP_CLASSES: Record<Lifecycle, string> = {
  issued: "bg-slate-100 text-slate-800",
  in_progress: "bg-gold/15 text-gold-dark",
  due: "bg-warn-bg text-[#8B5C1F]",
  due_date_over: "bg-alarm-bg text-alarm",
  reply_submitted: "bg-success-bg text-success",
  acknowledged: "bg-success/20 text-success",
  order_received: "bg-navy/10 text-navy",
  appeal_filed: "bg-gold/20 text-gold-dark",
  closed: "bg-slate-100 text-slate",
  on_hold: "bg-slate-100 text-slate",
};

export function lifecycleLabel(key: string): string {
  return (LIFECYCLE_LABELS as Record<string, string>)[key] ?? key;
}

export function lifecycleChipClass(key: string): string {
  return (
    (LIFECYCLE_CHIP_CLASSES as Record<string, string>)[key] ??
    "bg-slate-100 text-slate-800"
  );
}
