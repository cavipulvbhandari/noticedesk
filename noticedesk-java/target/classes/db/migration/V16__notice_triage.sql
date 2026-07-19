-- 0016_notice_triage.sql
-- Triage stage between parse and draft. The triage agent produces a
-- partner-facing summary + a document checklist; the partner attaches
-- supporting docs against each checklist item, and only then generates a
-- draft that consumes those docs as evidence (instead of the [ASSUMED]
-- markers v3 was patching over).
--
-- Triage is triggered manually by the partner clicking "Begin triage" on
-- the matter — not auto-fired after parse — so the LLM cost is only
-- incurred when the partner actually intends to work the notice.

-- ---- notice_triage --------------------------------------------------------
-- One row per notice. Status flows:
--   generating       -- LLM call in flight
--   ready_to_gather  -- summary + checklist persisted, partner uploading docs
--   ready_to_draft   -- (advisory) every required item resolved
--   drafted          -- a draft has been generated against this triage
-- The 'soft block' policy means the API never refuses to draft based on this
-- status; the UI uses it for the warning banner only.

CREATE TABLE IF NOT EXISTS notice_triage (
    notice_id       UUID PRIMARY KEY REFERENCES notices (notice_id) ON DELETE CASCADE,
    tenant_id       UUID NOT NULL REFERENCES tenants (tenant_id),
    summary         TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'ready_to_gather'
        CHECK (status IN ('generating', 'ready_to_gather', 'ready_to_draft', 'drafted')),
    prompt_version  TEXT NOT NULL,
    model           TEXT,
    provider_name   TEXT,
    input_tokens    INT,
    output_tokens   INT,
    generated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notice_triage_tenant_status
    ON notice_triage (tenant_id, status);

-- ---- notice_document_requirements ----------------------------------------
-- Checklist items the triage agent (or the partner, via add-custom) wants
-- before drafting. ``document_id`` is the link to the documents table once
-- the partner attaches a file against the item.

CREATE TABLE IF NOT EXISTS notice_document_requirements (
    requirement_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notice_id         UUID NOT NULL REFERENCES notices (notice_id) ON DELETE CASCADE,
    tenant_id         UUID NOT NULL REFERENCES tenants (tenant_id),
    label             TEXT NOT NULL,
    rationale         TEXT NOT NULL,
    doc_type          TEXT,
    is_required       BOOLEAN NOT NULL DEFAULT TRUE,
    status            TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'uploaded', 'not_applicable')),
    document_id       UUID REFERENCES documents (document_id) ON DELETE SET NULL,
    marked_na_reason  TEXT,
    position          INT NOT NULL DEFAULT 0,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notice_document_requirements_notice
    ON notice_document_requirements (notice_id, position);
CREATE INDEX IF NOT EXISTS idx_notice_document_requirements_doc
    ON notice_document_requirements (document_id)
    WHERE document_id IS NOT NULL;

-- ---- RLS -----------------------------------------------------------------

ALTER TABLE notice_triage ENABLE ROW LEVEL SECURITY;
ALTER TABLE notice_triage FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation ON notice_triage;
CREATE POLICY tenant_isolation ON notice_triage FOR ALL
    USING (tenant_id = current_tenant_id())
    WITH CHECK (tenant_id = current_tenant_id());

ALTER TABLE notice_document_requirements ENABLE ROW LEVEL SECURITY;
ALTER TABLE notice_document_requirements FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation ON notice_document_requirements;
CREATE POLICY tenant_isolation ON notice_document_requirements FOR ALL
    USING (tenant_id = current_tenant_id())
    WITH CHECK (tenant_id = current_tenant_id());

-- ---- Grants --------------------------------------------------------------

GRANT SELECT, INSERT, UPDATE, DELETE ON notice_triage              TO noticedesk_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON notice_document_requirements TO noticedesk_app;
