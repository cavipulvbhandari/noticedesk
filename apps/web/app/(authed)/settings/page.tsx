"use client";

import { useState } from "react";

import { ConnectorCard } from "@/components/settings/connector-card";
import { InfoModal } from "@/components/ui/info-modal";
import { cn } from "@/lib/cn";

const SECTIONS = [
  { key: "profile", label: "Profile" },
  { key: "firm", label: "Firm" },
  { key: "users", label: "Users & roles" },
  { key: "connectors", label: "Portal connectors" },
  { key: "audit", label: "Audit trail" },
  { key: "dpdp", label: "DPDP & consent" },
  { key: "billing", label: "Billing" },
  { key: "tokens", label: "API tokens" },
] as const;

type SectionKey = (typeof SECTIONS)[number]["key"];

export default function SettingsPage() {
  const [active, setActive] = useState<SectionKey>("connectors");
  const [info, setInfo] = useState<string | null>(null);

  return (
    <main className="mx-auto max-w-[1400px] px-10 py-8 pb-16">
      <header className="mb-7">
        <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-ink">
          Settings
        </p>
        <h1 className="font-serif text-[36px] font-medium tracking-tight text-navy-deep">
          Settings
        </h1>
      </header>

      <div className="grid grid-cols-1 gap-8 md:grid-cols-[240px_1fr]">
        <nav className="flex flex-col gap-0.5">
          {SECTIONS.map((s) => (
            <button
              key={s.key}
              type="button"
              onClick={() => setActive(s.key)}
              className={cn(
                "rounded-sm px-3.5 py-2.5 text-left text-[13px] font-medium transition-colors",
                active === s.key
                  ? "border border-slate-line bg-white font-semibold text-navy-deep"
                  : "text-slate hover:bg-paper hover:text-ink",
              )}
            >
              {s.label}
            </button>
          ))}
        </nav>

        <div>
          {active === "connectors" ? (
            <ConnectorsTab onSyncStub={(name) => setInfo(name)} />
          ) : (
            <StubTab section={SECTIONS.find((s) => s.key === active)?.label ?? ""} />
          )}
        </div>
      </div>

      <InfoModal
        open={info !== null}
        title={info ?? ""}
        eyebrow="Coming in Phase 2"
        onClose={() => setInfo(null)}
      >
        <p className="mb-3">
          This connector is part of the Phase 2 portal-sync rollout. Once the
          GSP and AA-framework integrations land, partners will be able to
          authorise per-registration consent here and watch notices stream in
          automatically.
        </p>
        <p className="text-slate">
          Phase 1 keeps ingestion via the inbox (drag-drop, mobile capture,
          email forwarding) which already routes by PAN reconciliation.
        </p>
      </InfoModal>
    </main>
  );
}

function ConnectorsTab({ onSyncStub }: { onSyncStub: (name: string) => void }) {
  return (
    <section>
      <h3 className="mb-1 font-serif text-[24px] font-semibold text-navy-deep">
        Portal connectors
      </h3>
      <p className="mb-6 max-w-[780px] text-[13.5px] leading-relaxed text-slate">
        Connect NoticeDesk to government portals to fetch notices automatically
        and reduce manual upload. All credentials are token-based; passwords
        are never stored. Per-client consent is captured before any fetch
        occurs.
      </p>

      <ConnectorCard
        iconLabel="G"
        iconClassName="bg-gold text-paper"
        name="GST Portal · via GSP"
        description="Fetch notices, orders, and DRC documents from gst.gov.in via a licensed GST Suvidha Provider (Cygnet, Masters India, or ClearTax). Per-GSTIN consent required; tokenised access, no password storage."
        meta={[
          { label: "Method", value: "GSP-mediated API" },
          { label: "ETA", value: "Phase 2" },
        ]}
        status="coming-soon"
        statusLabel="Coming Soon · Phase 2"
        ctaLabel="Configure"
        ctaDisabled
        onCta={() => onSyncStub("GST Portal · via GSP")}
      />

      <ConnectorCard
        iconLabel="IT"
        iconClassName="bg-navy text-gold"
        name="Income Tax Portal"
        description="Direct fetch of notices from incometax.gov.in is currently constrained — the portal does not expose a public API for assessee data. Integration via the Account Aggregator framework is in active development."
        meta={[
          { label: "Method", value: "AA Framework (planned)" },
          { label: "ETA", value: "Q3 2026" },
          { label: "Fallback", value: "Manual upload + email" },
        ]}
        status="coming-soon"
        statusLabel="Coming soon · Q3 2026"
        ctaLabel="Configure"
        ctaDisabled
        onCta={() => onSyncStub("Income Tax Portal")}
      />

      <ConnectorCard
        iconLabel="@"
        iconClassName="bg-success text-paper"
        name="Email Forwarding"
        description={
          <>
            Notices arriving in your firm inbox can be forwarded to{" "}
            <span className="font-mono text-gold-dark">notices+mehta@noticedesk.in</span>.
            They are auto-routed by PAN reconciliation just like uploads.
          </>
        }
        meta={[
          { label: "Status", value: "Active" },
          { label: "Routed by", value: "PAN reconciliation" },
        ]}
        status="connected"
        statusLabel="Connected"
        ctaLabel="Manage"
        onCta={() => onSyncStub("Email Forwarding")}
      />

      <ConnectorCard
        iconLabel="W"
        iconClassName="bg-[#25D366] text-white"
        name="WhatsApp Business API"
        description="Forward notices via WhatsApp; receive draft summaries on your phone within 90 seconds. Requires BSP onboarding (Gupshup or Interakt)."
        meta={[
          { label: "Method", value: "Gupshup BSP" },
          { label: "Status", value: "Phase 3 build" },
        ]}
        status="coming-soon"
        statusLabel="Coming Q4 2026"
        faded
      />

      <aside className="mt-6 rounded-sm border-l-[3px] border-gold bg-gold/5 px-5 py-4 font-serif text-[13.5px] italic leading-relaxed text-ink-soft">
        <p className="mb-2 text-[10px] font-sans font-bold uppercase not-italic tracking-[0.14em] text-gold-dark">
          Extensibility · Architectural note
        </p>
        Every connector is a pluggable adapter behind a uniform{" "}
        <span className="font-mono text-[12.5px] not-italic text-gold-dark">PortalConnector</span>{" "}
        interface. Adding a new source — a new GSP provider, a state-specific
        portal, the AA framework once it matures — requires no schema change.
        Notices simply land with{" "}
        <span className="font-mono text-[12.5px] not-italic">ingest_channel</span> set to the
        new connector&rsquo;s identifier. The PAN-centric routing logic and
        the dashboard surfaces remain unchanged. We invested in this
        abstraction up front because portal access in India is fragmented and
        shifts every two to three years; the product must accommodate change
        without rebuilding.
      </aside>
    </section>
  );
}

function StubTab({ section }: { section: string }) {
  return (
    <section className="rounded-md border border-dashed border-slate-line bg-white px-6 py-12 text-center">
      <p className="mb-2 font-serif text-[18px] font-semibold text-navy-deep">
        {section}
      </p>
      <p className="mx-auto max-w-md font-serif text-[14px] italic text-slate">
        Coming in Phase 2. The Portal Connectors tab is the only fully wired
        settings surface in Phase 1; the rest of the rail is reserved so the
        information architecture stays stable.
      </p>
    </section>
  );
}
