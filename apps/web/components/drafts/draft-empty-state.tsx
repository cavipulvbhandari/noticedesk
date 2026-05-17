"use client";

import { useState } from "react";

import { DraftProgressCard } from "@/components/drafts/draft-progress-card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/cn";

type Tone = "formal" | "assertive" | "conciliatory";

interface Props {
  busy: boolean;
  error: string | null;
  onGenerate: (tone: Tone, instructions: string, includeCross: boolean) => Promise<void>;
}

const TONE_OPTIONS: Array<{ value: Tone; label: string; desc: string }> = [
  {
    value: "formal",
    label: "Formal",
    desc: "Third-person, measured, courteous — the default for first-round replies.",
  },
  {
    value: "assertive",
    label: "Assertive",
    desc: "Direct rebuttal where law + facts support it; still courteous.",
  },
  {
    value: "conciliatory",
    label: "Conciliatory",
    desc: "Emphasise willingness to comply; request indulgence on procedure.",
  },
];

export function DraftEmptyState({ busy, error, onGenerate }: Props) {
  const [tone, setTone] = useState<Tone>("formal");
  const [instructions, setInstructions] = useState("");
  const [includeCross, setIncludeCross] = useState(false);

  if (busy) {
    return <DraftProgressCard busy />;
  }

  return (
    <div className="rounded-md border border-slate-line bg-white px-8 py-10">
      <p className="mb-1 text-[10px] font-bold uppercase tracking-[0.14em] text-gold-dark">
        Draft reply
      </p>
      <h2 className="mb-2 font-serif text-[24px] font-semibold text-navy-deep">
        Generate the first draft
      </h2>
      <p className="mb-6 max-w-[640px] font-serif text-[14px] italic text-slate">
        The drafting agent reads the parsed notice, this registration&rsquo;s
        prior matters, attached documents, and produces a 15-section reply
        with verified citations. Sibling registrations are deliberately
        excluded so the factual matrix stays clean.
      </p>

      <fieldset className="mb-6">
        <legend className="mb-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-slate">
          Tone
        </legend>
        <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
          {TONE_OPTIONS.map((o) => (
            <label
              key={o.value}
              className={cn(
                "cursor-pointer rounded-sm border bg-white px-3.5 py-3 transition-colors",
                tone === o.value
                  ? "border-gold ring-1 ring-gold"
                  : "border-slate-line hover:border-slate",
              )}
            >
              <input
                type="radio"
                name="tone"
                value={o.value}
                checked={tone === o.value}
                onChange={() => setTone(o.value)}
                className="sr-only"
              />
              <p className="font-serif text-[14px] font-semibold text-navy-deep">
                {o.label}
              </p>
              <p className="mt-1 text-[11.5px] leading-relaxed text-slate">{o.desc}</p>
            </label>
          ))}
        </div>
      </fieldset>

      <label className="mb-2 block text-[11px] font-semibold uppercase tracking-[0.08em] text-slate">
        Partner instructions (optional)
      </label>
      <textarea
        value={instructions}
        onChange={(e) => setInstructions(e.target.value)}
        rows={3}
        placeholder="e.g. Lean on the limitation point. Officer is open to reconciliation-based closure."
        className="mb-4 w-full rounded-sm border border-slate-line bg-white px-3.5 py-2 text-[13px] outline-none focus:border-gold"
      />

      <label className="mb-6 flex items-start gap-2.5 text-[12.5px] text-ink-soft">
        <input
          type="checkbox"
          checked={includeCross}
          onChange={(e) => setIncludeCross(e.target.checked)}
          className="mt-0.5"
        />
        <span>
          Include cross-registration context (only check if facts from a
          sibling state / law are genuinely relevant — they land in their own
          Section 09 and never in the factual matrix).
        </span>
      </label>

      {error ? (
        <p className="mb-4 rounded border border-alarm/30 bg-alarm-bg px-3 py-2 text-sm text-alarm">
          {error}
        </p>
      ) : null}

      <Button
        variant="gold"
        size="lg"
        disabled={busy}
        onClick={() => onGenerate(tone, instructions, includeCross)}
      >
        Generate draft
      </Button>
    </div>
  );
}

