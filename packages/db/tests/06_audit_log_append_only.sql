-- 06_audit_log_append_only.sql — UPDATE / DELETE / TRUNCATE blocked on audit_logs.

INSERT INTO tenants (legal_name) VALUES ('Test Firm') RETURNING tenant_id \gset

-- Insert is allowed.
SELECT assert_succeeds(format($sql$
    INSERT INTO audit_logs (tenant_id, action_type, entity_type, after_state)
    VALUES (%L, 'create', 'tenant', '{"foo": "bar"}'::JSONB)
$sql$, :'tenant_id'));

SELECT assert_raises(format($sql$
    UPDATE audit_logs SET action_type = 'tampered' WHERE tenant_id = %L
$sql$, :'tenant_id'), 'append-only');

SELECT assert_raises(format($sql$
    DELETE FROM audit_logs WHERE tenant_id = %L
$sql$, :'tenant_id'), 'append-only');

SELECT assert_raises('TRUNCATE audit_logs', 'append-only');
