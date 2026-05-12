"use client";

import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast";
import { editDraftSection, type DraftSection } from "@/lib/api";
import { cn } from "@/lib/cn";

interface Props {
  draftId: string;
  sections: DraftSection[];
  internalPartnerNote: string | null;
  onSaved: (newDraftId: string) => void;
}

// Editable per-section panel. Each section's body_html lives in a
// contentEditable div; the partner clicks "Edit", makes changes, clicks Save
// → the server creates a new draft version and the parent flips to it.
export function DraftPane({ draftId, sections, internalPartnerNote, onSaved }: Props) {
  return (
    <div className="overflow-y-auto px-9 py-8 font-serif text-[14px] leading-relaxed text-ink">
      {sections.map((s) => (
        <SectionEditor
          key={`${draftId}-${s.num}`}
          draftId={draftId}
          section={s}
          onSaved={onSaved}
        />
      ))}
      {internalPartnerNote ? (
        <aside className="mt-8 rounded-sm border border-dashed border-gold bg-gold/5 px-5 py-4">
          <p className="mb-1 text-[10px] font-bold uppercase tracking-[0.12em] text-gold-dark">
            Internal partner note · never client-facing
          </p>
          <p className="font-serif text-[13.5px] italic leading-relaxed text-ink-soft">
            {internalPartnerNote}
          </p>
        </aside>
      ) : null}
    </div>
  );
}

function SectionEditor({
  draftId,
  section,
  onSaved,
}: {
  draftId: string;
  section: DraftSection;
  onSaved: (newDraftId: string) => void;
}) {
  const { toast } = useToast();
  const ref = useRef<HTMLDivElement>(null);
  const [editing, setEditing] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (ref.current) {
      ref.current.innerHTML = section.body_html;
    }
  }, [section.body_html, editing]);

  async function handleSave() {
    if (!ref.current) return;
    setBusy(true);
    try {
      const res = await editDraftSection(draftId, {
        section_num: section.num,
        body_html: ref.current.innerHTML,
      });
      if (res.changed) {
        toast(`Section ${section.num} saved as v${res.version}`, "success");
        onSaved(res.draft_id);
      } else {
        toast("No changes detected", "info");
      }
      setEditing(false);
    } catch (e: unknown) {
      toast(e instanceof Error ? e.message : "save failed", "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="mb-8">
      <div className="mb-2 flex items-baseline justify-between gap-3">
        <div>
          <p className="text-[9px] font-bold uppercase tracking-[0.18em] text-gold-dark">
            Section {String(section.num).padStart(2, "0")}
          </p>
          <h3 className="font-serif text-[18px] font-semibold text-navy-deep">
            {section.title}
          </h3>
        </div>
        {editing ? (
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setEditing(false)}
              disabled={busy}
            >
              Cancel
            </Button>
            <Button variant="gold" size="sm" onClick={handleSave} disabled={busy}>
              {busy ? "Saving…" : "Save as new version"}
            </Button>
          </div>
        ) : (
          <Button variant="ghost" size="sm" onClick={() => setEditing(true)}>
            Edit
          </Button>
        )}
      </div>
      <div
        ref={ref}
        className={cn(
          "draft-body rounded-sm px-4 py-3 transition-colors",
          editing
            ? "border border-gold bg-paper-warm/40 outline-none ring-2 ring-gold/30 focus:bg-white"
            : "border border-transparent",
        )}
        contentEditable={editing}
        suppressContentEditableWarning
      />
    </section>
  );
}
