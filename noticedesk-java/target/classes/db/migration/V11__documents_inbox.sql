-- 0011_documents_inbox.sql
-- The unified inbox for inbound notice documents.
--
-- Sprint 2 fills ocr_* and ingest_* columns. parse_status, parsed_to_notice_id,
-- routing_status, and routing_anomaly_details are reserved for Sprint 3 and
-- left at their 'pending' defaults until then.

CREATE TABLE IF NOT EXISTS documents_inbox (
    inbox_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id             UUID NOT NULL REFERENCES tenants (tenant_id) ON DELETE CASCADE,
    uploaded_by_user_id   UUID REFERENCES users (user_id),
    original_filename     TEXT NOT NULL,
    file_hash             TEXT NOT NULL,
    file_size_bytes       BIGINT NOT NULL,
    page_count            INT,
    mime_type             TEXT,
    s3_key                TEXT NOT NULL,

    ocr_status            TEXT NOT NULL DEFAULT 'pending'
        CHECK (ocr_status IN ('pending', 'in_progress', 'completed', 'failed')),
    ocr_text              TEXT,
    ocr_layout_json       JSONB,
    ocr_provider_used     TEXT,
    ocr_started_at        TIMESTAMPTZ,
    ocr_completed_at      TIMESTAMPTZ,
    ocr_error             TEXT,

    ingest_channel        TEXT NOT NULL CHECK (ingest_channel IN (
        'web_upload', 'mobile_capture', 'email',
        'gst_portal_gsp', 'it_portal_aa', 'whatsapp'
    )),
    ingest_metadata       JSONB,

    parse_status          TEXT NOT NULL DEFAULT 'pending'
        CHECK (parse_status IN ('pending', 'in_progress', 'completed', 'failed', 'needs_review')),
    parsed_to_notice_id   UUID REFERENCES notices (notice_id) ON DELETE SET NULL,
    routing_status        TEXT NOT NULL DEFAULT 'pending'
        CHECK (routing_status IN (
            'pending', 'routed', 'client_not_found',
            'new_gst_registration_detected', 'pan_gstin_mismatch',
            'no_identifier_found', 'manual_assignment'
        )),
    routing_anomaly_details JSONB,

    uploaded_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT file_hash_format CHECK (file_hash ~ '^[a-f0-9]{64}$'),
    CONSTRAINT file_size_positive CHECK (file_size_bytes > 0)
);

CREATE INDEX IF NOT EXISTS idx_inbox_tenant_status   ON documents_inbox (tenant_id, ocr_status);
CREATE INDEX IF NOT EXISTS idx_inbox_tenant_uploaded ON documents_inbox (tenant_id, uploaded_at DESC);
CREATE INDEX IF NOT EXISTS idx_inbox_parse_status    ON documents_inbox (tenant_id, parse_status);
CREATE INDEX IF NOT EXISTS idx_inbox_file_hash       ON documents_inbox (tenant_id, file_hash);

-- RLS: scope every row to its owning tenant, same pattern as Sprint 1 tables.
ALTER TABLE documents_inbox ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents_inbox FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation ON documents_inbox;
CREATE POLICY tenant_isolation ON documents_inbox
    FOR ALL
    USING (tenant_id = current_tenant_id())
    WITH CHECK (tenant_id = current_tenant_id());

-- Auto-touch updated_at on UPDATE. clock_timestamp() (not NOW()) so the
-- value advances even when several updates happen in the same transaction.
CREATE OR REPLACE FUNCTION touch_documents_inbox_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := clock_timestamp();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_documents_inbox_touch ON documents_inbox;
CREATE TRIGGER trg_documents_inbox_touch
    BEFORE UPDATE ON documents_inbox
    FOR EACH ROW EXECUTE FUNCTION touch_documents_inbox_updated_at();
