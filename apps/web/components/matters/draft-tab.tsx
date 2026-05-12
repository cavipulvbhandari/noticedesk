"use client";

import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast";

// Stub per the brief: "showing 'Generate draft' button (full implementation
// in Sprint 5)". Clicking it explains what's coming so partners don't think
// the button is broken.
export function DraftTab() {
  const { toast } = useToast();
  return (
    <div className="rounded-md border border-slate-line bg-white px-6 py-10 text-center">
      <p className="mb-2 font-serif text-[18px] font-semibold text-navy-deep">
        Draft a reply
      </p>
      <p className="mx-auto mb-5 max-w-md font-serif text-[14px] italic text-slate">
        In Sprint 5 the drafting agent will read the parsed notice, pull
        relevant authorities, and produce a citation-verified draft you can
        review and export to Word.
      </p>
      <Button
        variant="gold"
        onClick={() =>
          toast(
            "Draft generation arrives in Sprint 5 (citation-verified output + Word export)",
            "info",
          )
        }
      >
        Generate draft
      </Button>
    </div>
  );
}
