-- V18: add soft-delete support to documents table
-- Required by PATCH /v1/documents/{id} and DELETE /v1/documents/{id}

ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_documents_deleted_at
    ON documents (tenant_id, deleted_at)
    WHERE deleted_at IS NOT NULL;
