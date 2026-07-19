-- 0014_clients_soft_delete.sql
-- Sprint 4 slice 3: partners can soft-delete a client.
--
-- The brief calls out:
--   DELETE /v1/clients/{id} — soft delete (sets a deleted_at field;
--   partner role only; logged at risk_tier=2)
--
-- Hard delete is wrong here — every notice and audit row points back to the
-- client, and reversing an accidental delete in front of a partner under
-- deadline pressure beats reconstructing rows from S3 backups. The unique
-- constraint on (tenant_id, pan) becomes a partial unique on rows where
-- deleted_at IS NULL so a partner can re-add a client with the same PAN
-- after a soft-delete.

ALTER TABLE clients
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;

-- Replace the full unique constraint with a partial unique index that
-- ignores soft-deleted rows. The named CHECK / UNIQUE constraint from 0003
-- must be dropped first; the partial index then provides equivalent
-- protection for live rows.
ALTER TABLE clients DROP CONSTRAINT IF EXISTS clients_tenant_pan_unique;

CREATE UNIQUE INDEX IF NOT EXISTS idx_clients_tenant_pan_active
    ON clients (tenant_id, pan)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_clients_deleted_at
    ON clients (tenant_id, deleted_at)
    WHERE deleted_at IS NOT NULL;
