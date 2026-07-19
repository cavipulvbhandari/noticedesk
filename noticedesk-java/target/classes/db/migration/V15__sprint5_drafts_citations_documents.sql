-- 0015_sprint5_drafts_citations_documents.sql
-- Sprint 5 reconciliation: align documents / drafts / citations with the
-- drafting-engine brief. The original Sprint 1 tables (migration 0005)
-- were schema sketches; the drafting agent needs richer columns to
-- persist the 15-section structure, paragraph→source map, edit history,
-- citation cache details, and document extracted text.
--
-- Backwards-compatible: every change is additive (ADD COLUMN IF NOT EXISTS,
-- DROP CONSTRAINT IF EXISTS + recreate with a wider value set). Existing
-- rows survive — there aren't any yet, but the migration is safe to run
-- against a populated database.

-- ---- documents ------------------------------------------------------------

ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS filename        TEXT,
    ADD COLUMN IF NOT EXISTS mime_type       TEXT,
    ADD COLUMN IF NOT EXISTS size_bytes      INT,
    ADD COLUMN IF NOT EXISTS extracted_text  TEXT,
    ADD COLUMN IF NOT EXISTS metadata        JSONB;

-- Brief requires filename NOT NULL going forward. Backfill with a placeholder
-- so the constraint applies to all rows including any historical ones.
UPDATE documents
SET filename = COALESCE(filename,
    'document_' || REPLACE(document_id::TEXT, '-', '') || '.bin')
WHERE filename IS NULL;
ALTER TABLE documents
    ALTER COLUMN filename SET NOT NULL;

CREATE INDEX IF NOT EXISTS idx_documents_matter_lifecycle
    ON documents (matter_id, lifecycle_stage);
CREATE INDEX IF NOT EXISTS idx_documents_file_hash
    ON documents (tenant_id, file_hash)
    WHERE file_hash IS NOT NULL;

-- ---- drafts --------------------------------------------------------------

ALTER TABLE drafts
    ADD COLUMN IF NOT EXISTS tone                     TEXT,
    ADD COLUMN IF NOT EXISTS sections                 JSONB,
    ADD COLUMN IF NOT EXISTS citation_summary         JSONB,
    ADD COLUMN IF NOT EXISTS internal_partner_note    TEXT,
    ADD COLUMN IF NOT EXISTS generated_at             TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS generated_by_user_id     UUID REFERENCES users (user_id);

-- ``content`` in 0005 was the catch-all; the brief replaces it with a
-- structured ``sections`` JSONB array. Backfill sections from content for
-- any pre-existing draft rows so the rest of the app can read uniformly.
UPDATE drafts
SET sections = COALESCE(sections, content, '[]'::JSONB)
WHERE sections IS NULL;

-- ``generated_at`` mirrors ``created_at`` for back-fill so audit/UI can rely
-- on a single timestamp regardless of which column existed at insert time.
UPDATE drafts SET generated_at = COALESCE(generated_at, created_at);

-- citation_status_summary (0005) → citation_summary (brief). Mirror.
UPDATE drafts SET citation_summary = COALESCE(citation_summary, citation_status_summary)
WHERE citation_summary IS NULL AND citation_status_summary IS NOT NULL;

ALTER TABLE drafts
    DROP CONSTRAINT IF EXISTS drafts_tone_check;
ALTER TABLE drafts
    ADD CONSTRAINT drafts_tone_check
    CHECK (tone IS NULL OR tone IN ('formal', 'assertive', 'conciliatory'));

CREATE UNIQUE INDEX IF NOT EXISTS uq_drafts_matter_version
    ON drafts (matter_id, version);

CREATE INDEX IF NOT EXISTS idx_drafts_matter_generated
    ON drafts (matter_id, generated_at DESC);

-- ---- citations -----------------------------------------------------------

-- Brief renames `date` → `decided_date` (more explicit) and adds verifier
-- audit columns. Keep both columns for now; new code writes to
-- ``decided_date`` while old rows keep ``date`` populated.
ALTER TABLE citations
    ADD COLUMN IF NOT EXISTS decided_date                  DATE,
    ADD COLUMN IF NOT EXISTS verified_paragraph_text       TEXT,
    ADD COLUMN IF NOT EXISTS proposition_match_confidence  NUMERIC,
    ADD COLUMN IF NOT EXISTS action_taken                  TEXT;

UPDATE citations SET decided_date = COALESCE(decided_date, date) WHERE decided_date IS NULL;

ALTER TABLE citations
    DROP CONSTRAINT IF EXISTS citations_action_taken_check;
ALTER TABLE citations
    ADD CONSTRAINT citations_action_taken_check
    CHECK (action_taken IS NULL OR action_taken IN ('passed', 'flagged', 'stripped'));

-- Reset the status CHECK to the Sprint 5 vocabulary. The Sprint 1 set
-- (VERIFIED / VERIFIED_PARTIAL / UNVERIFIED / SUPERSEDED / DISTINGUISHED /
-- UNDER_STAY) included Tier 3 outcomes the Phase 1 verifier never returns;
-- drop SUPERSEDED / DISTINGUISHED / UNDER_STAY because the Phase 1 free
-- IndianKanoon API can't produce them. The Phase 2 migration will widen
-- it again when Tier 2/3 (Taxmann/SCC + firm library) come online.
ALTER TABLE citations DROP CONSTRAINT IF EXISTS citations_status_check;
ALTER TABLE citations
    ADD CONSTRAINT citations_status_check
    CHECK (status IN ('VERIFIED', 'VERIFIED_PARTIAL', 'UNVERIFIED', 'STRIPPED'));

ALTER TABLE citations
    ALTER COLUMN verification_tier SET DEFAULT 1;

CREATE INDEX IF NOT EXISTS idx_citations_draft_status
    ON citations (draft_id, status);
CREATE INDEX IF NOT EXISTS idx_citations_case_name
    ON citations (tenant_id, LOWER(case_name))
    WHERE case_name IS NOT NULL;

-- ---- citation cache (30-day re-verify rule) ------------------------------

-- The Phase 1 verifier caches IndianKanoon hits by case_name + citation_string
-- so repeat verifications across drafts don't hammer the free API. The cache
-- is tenant-agnostic (case law is public) but we still scope reads through
-- the API; storing it as a separate table simplifies retention policy.
CREATE TABLE IF NOT EXISTS citation_cache (
    cache_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_name_normalized  TEXT NOT NULL,
    citation_string       TEXT,
    provider              TEXT NOT NULL,  -- 'indiankanoon', 'stub'
    status                TEXT NOT NULL
        CHECK (status IN ('VERIFIED', 'VERIFIED_PARTIAL', 'UNVERIFIED')),
    source_url            TEXT,
    verified_paragraph_text TEXT,
    raw_response          JSONB,
    verified_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (case_name_normalized, citation_string, provider)
);
CREATE INDEX IF NOT EXISTS idx_citation_cache_verified_at
    ON citation_cache (verified_at DESC);

-- citation_cache is NOT RLS-protected by design (case law is public domain)
-- so we don't add a tenant_id column or policy. The API never returns the
-- cache table directly; it joins through citations which IS RLS-protected.

-- Grant noticedesk_app the same DML it has on the rest of public.
GRANT SELECT, INSERT, UPDATE, DELETE ON citation_cache TO noticedesk_app;
