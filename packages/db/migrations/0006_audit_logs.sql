-- 0006_audit_logs.sql
-- Append-only audit log: UPDATE and DELETE blocked at trigger level.

CREATE TABLE IF NOT EXISTS audit_logs (
    log_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL,
    user_id             UUID,
    timestamp           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    action_type         TEXT,
    entity_type         TEXT,
    entity_id           UUID,
    before_state        JSONB,
    after_state         JSONB,
    ip_address          INET,
    user_agent          TEXT,
    risk_tier           INT,
    approval_required   BOOLEAN,
    approval_granted_by UUID,
    approval_reason     TEXT
);
CREATE INDEX IF NOT EXISTS idx_audit_logs_tenant_time ON audit_logs (tenant_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity     ON audit_logs (entity_type, entity_id);

CREATE OR REPLACE FUNCTION block_audit_log_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'audit_logs is append-only; % is not permitted', TG_OP;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_audit_logs_no_update ON audit_logs;
CREATE TRIGGER trg_audit_logs_no_update
    BEFORE UPDATE ON audit_logs
    FOR EACH ROW EXECUTE FUNCTION block_audit_log_mutation();

DROP TRIGGER IF EXISTS trg_audit_logs_no_delete ON audit_logs;
CREATE TRIGGER trg_audit_logs_no_delete
    BEFORE DELETE ON audit_logs
    FOR EACH ROW EXECUTE FUNCTION block_audit_log_mutation();

DROP TRIGGER IF EXISTS trg_audit_logs_no_truncate ON audit_logs;
CREATE TRIGGER trg_audit_logs_no_truncate
    BEFORE TRUNCATE ON audit_logs
    FOR EACH STATEMENT EXECUTE FUNCTION block_audit_log_mutation();
