-- 0005_documents_drafts_citations.sql

CREATE TABLE IF NOT EXISTS documents (
    document_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                UUID NOT NULL REFERENCES tenants (tenant_id) ON DELETE RESTRICT,
    matter_id                UUID NOT NULL REFERENCES matters (matter_id) ON DELETE RESTRICT,
    document_type            TEXT,
    lifecycle_stage          TEXT CHECK (lifecycle_stage IN (
        'requested', 'received', 'validated', 'used_in_draft',
        'approved', 'submitted', 'acknowledged', 'referenced_in_appeal'
    )),
    file_hash                TEXT,
    s3_key                   TEXT,
    version                  INT NOT NULL DEFAULT 1,
    uploaded_by_user_id      UUID REFERENCES users (user_id),
    uploaded_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    linked_to_paragraph_ids  UUID[],
    annexure_index_position  INT
);
CREATE INDEX IF NOT EXISTS idx_documents_matter ON documents (matter_id);

CREATE TABLE IF NOT EXISTS drafts (
    draft_id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                   UUID NOT NULL REFERENCES tenants (tenant_id) ON DELETE RESTRICT,
    matter_id                   UUID NOT NULL REFERENCES matters (matter_id) ON DELETE RESTRICT,
    version                     INT NOT NULL DEFAULT 1,
    status                      TEXT NOT NULL CHECK (status IN ('draft', 'partner_review', 'client_review', 'final', 'filed')),
    generated_by_agent_version  TEXT,
    model_used                  TEXT,
    prompt_version              TEXT,
    content                     JSONB NOT NULL,
    citation_status_summary     JSONB,
    edits_log                   JSONB,
    approvals_log               JSONB,
    paragraph_to_source_map     JSONB,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_drafts_matter ON drafts (matter_id);

CREATE TABLE IF NOT EXISTS citations (
    citation_id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                    UUID NOT NULL REFERENCES tenants (tenant_id) ON DELETE RESTRICT,
    draft_id                     UUID REFERENCES drafts (draft_id) ON DELETE CASCADE,
    case_name                    TEXT,
    citation_string              TEXT,
    court_or_forum               TEXT,
    date                         DATE,
    paragraph_referenced         TEXT,
    proposition_for_which_cited  TEXT,
    status                       TEXT CHECK (status IN (
        'VERIFIED', 'VERIFIED_PARTIAL', 'UNVERIFIED', 'SUPERSEDED', 'DISTINGUISHED', 'UNDER_STAY'
    )),
    source_url                   TEXT,
    verification_tier            INT,
    verified_at                  TIMESTAMPTZ,
    blocked_from_export          BOOLEAN NOT NULL DEFAULT FALSE,
    partner_override_reason      TEXT
);
CREATE INDEX IF NOT EXISTS idx_citations_draft ON citations (draft_id);
