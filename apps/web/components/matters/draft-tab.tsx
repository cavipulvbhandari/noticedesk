"use client";

import { useCallback, useEffect, useState } from "react";

import { CompareVersionsModal } from "@/components/drafts/compare-versions-modal";
import { DraftEmptyState } from "@/components/drafts/draft-empty-state";
import { DraftPane } from "@/components/drafts/draft-pane";
import { DraftProgressCard } from "@/components/drafts/draft-progress-card";
import { DraftToolbar } from "@/components/drafts/draft-toolbar";
import { VerificationPanel } from "@/components/drafts/verification-panel";
import { useToast } from "@/components/ui/toast";
import {
  fetchDraft,
  fetchDraftVersions,
  generateDraft,
  type DraftDetail,
  type DraftSummary,
} from "@/lib/api";

interface Props {
  noticeId: string;
  matterId: string;
}

export function DraftTab({ noticeId, matterId }: Props) {
  const { toast } = useToast();
  const [versions, setVersions] = useState<DraftSummary[]>([]);
  const [draft, setDraft] = useState<DraftDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [compareOpen, setCompareOpen] = useState(false);

  const loadVersions = useCallback(async (): Promise<DraftSummary[]> => {
    const res = await fetchDraftVersions(matterId);
    setVersions(res.drafts);
    return res.drafts;
  }, [matterId]);

  const loadDraft = useCallback(async (draftId: string) => {
    const d = await fetchDraft(draftId);
    setDraft(d);
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const list = await loadVersions();
        if (cancelled) return;
        if (list.length > 0) {
          await loadDraft(list[0]!.draft_id);
        }
      } catch (e: unknown) {
        if (!cancelled) setError(e instanceof Error ? e.message : "failed to load draft");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [loadVersions, loadDraft]);

  async function handleGenerate(
    tone: "formal" | "assertive" | "conciliatory",
    instructions: string,
    includeCross: boolean,
  ) {
    setBusy(true);
    setError(null);
    try {
      const res = await generateDraft(noticeId, {
        tone,
        partner_instructions: instructions,
        include_cross_registration: includeCross,
      });
      const list = await loadVersions();
      await loadDraft(res.draft_id);
      toast(
        `Draft v${res.version} generated · ${res.citation_summary.verified ?? 0} verified, ${res.citation_summary.stripped ?? 0} stripped`,
        "success",
      );
      void list;
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "draft failed");
    } finally {
      setBusy(false);
    }
  }

  function handleExport(mode: "filing" | "client" | "internal") {
    if (!draft) return;
    // Sprint 5 slice 7 wires the actual /v1/drafts/{id}/export endpoint.
    window.open(`/api/drafts/${draft.draft_id}/export?mode=${mode}`, "_blank");
  }

  if (loading) {
    return <p className="py-12 text-center font-serif italic text-slate">Loading draft…</p>;
  }

  if (versions.length === 0 || !draft) {
    return (
      <DraftEmptyState
        busy={busy}
        error={error}
        onGenerate={handleGenerate}
      />
    );
  }

  return (
    <div className="overflow-hidden rounded-md border border-slate-line bg-white">
      <DraftToolbar
        current={draft}
        versions={versions}
        onPickVersion={(id) => void loadDraft(id)}
        onCompare={() => setCompareOpen(true)}
        onRegenerate={() => {
          // Reuse the same handler as first-generation; the toolbar is
          // disabled while busy and the body below swaps to the progress
          // card so partners see the same multi-step status as a first run.
          void handleGenerate(
            (draft.tone as "formal" | "assertive" | "conciliatory") || "formal",
            "",
            false,
          );
        }}
        onExport={handleExport}
        busy={busy}
      />
      {busy ? (
        // Regenerate path: swap the split-pane for the same progress card
        // the first-generation flow shows. Title makes it clear the
        // existing draft is being replaced, not lost — the previous version
        // is still in the version dropdown when this completes.
        <div className="px-6 py-6">
          <DraftProgressCard
            busy
            eyebrow="Regenerating draft"
            title={`Replacing v${draft.version} with a fresh generation — previous version stays in history`}
          />
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-[1.6fr_1fr]" style={{ minHeight: 600 }}>
          <DraftPane
            draftId={draft.draft_id}
            sections={draft.sections}
            internalPartnerNote={draft.internal_partner_note}
            onSaved={(newId) => {
              void (async () => {
                await loadVersions();
                await loadDraft(newId);
              })();
            }}
          />
          <VerificationPanel draft={draft} />
        </div>
      )}

      {error ? (
        <p className="mx-6 mb-4 rounded border border-alarm/30 bg-alarm-bg px-3 py-2 text-sm text-alarm">
          {error}
        </p>
      ) : null}

      <CompareVersionsModal
        open={compareOpen}
        versions={versions}
        currentDraftId={draft.draft_id}
        onClose={() => setCompareOpen(false)}
      />
    </div>
  );
}
