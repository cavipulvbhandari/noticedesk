-- 0018_training_data.sql
-- Training-data capture for fine-tuning.
--
-- training_signal records the partner's implicit verdict on a draft:
--   'positive'  — partner exported (filed) this draft, meaning it was good
--                 enough to send. Set by GET /v1/drafts/{id}/export.
--   'negative'  — partner generated a replacement draft without ever
--                 exporting this one. Set by POST /v1/notices/{id}/draft
--                 on the previous unlabeled draft(s) for the same matter.
--   NULL        — unlabeled (most in-flight drafts; draft still open for
--                 editing or partner hasn't exported yet).
--
-- This column is the only schema change needed: the edits_log JSONB
-- already exists and we simply start writing 'before_html' into every
-- new section-edit entry so the pre-edit HTML is recoverable without
-- joining the prior draft version.

ALTER TABLE drafts
    ADD COLUMN IF NOT EXISTS training_signal TEXT
        CHECK (training_signal IN ('positive', 'negative'));

-- Sparse index — only rows that have been labeled need to be scanned
-- during training-export queries, which filter on training_signal IS NOT NULL.
CREATE INDEX IF NOT EXISTS idx_drafts_training
    ON drafts (tenant_id, training_signal)
    WHERE training_signal IS NOT NULL;
