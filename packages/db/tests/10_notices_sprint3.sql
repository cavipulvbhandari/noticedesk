-- 10_notices_sprint3.sql — verify Sprint 3 additions to notices table.

INSERT INTO tenants (legal_name) VALUES ('Routing Firm') RETURNING tenant_id AS tid \gset

SELECT set_config('app.current_tenant', :'tid', true);

INSERT INTO clients (tenant_id, pan, legal_name)
VALUES (:'tid', 'AAACX1234F', 'Acme Pvt Ltd')
RETURNING client_id AS cid \gset

INSERT INTO client_registrations (tenant_id, client_id, registration_type, identifier_value)
VALUES (:'tid', :'cid', 'IT', 'AAACX1234F')
RETURNING registration_id AS rid \gset

INSERT INTO matters (tenant_id, client_id, registration_id, law, financial_year, assessment_year)
VALUES (:'tid', :'cid', :'rid', 'IT', '2022-23', '2023-24')
RETURNING matter_id AS mid \gset

-- opening_date should auto-fill to today via the new default.
-- Use plpgsql so the assertion is evaluated at runtime, not constant-folded.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM matters WHERE opening_date = CURRENT_DATE
    ) THEN
        RAISE EXCEPTION 'matters.opening_date default did not apply';
    END IF;
END $$;

-- Insert a notice using the Sprint 3 columns.
INSERT INTO documents_inbox (
    tenant_id, original_filename, file_hash, file_size_bytes,
    s3_key, mime_type, ingest_channel
) VALUES (
    :'tid', 'n.pdf',
    'abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789',
    1024, 'tenants/x/inbox/y/n.pdf', 'application/pdf', 'web_upload'
) RETURNING inbox_id AS iid \gset

INSERT INTO notices (
    tenant_id, matter_id, client_id, registration_id, law,
    document_type, issue_date, due_date, demand_amount,
    ingest_channel, source_inbox_id, pan_gstin_reconciliation_status
) VALUES (
    :'tid', :'mid', :'cid', :'rid', 'IT',
    'IT_142(1)', CURRENT_DATE, CURRENT_DATE + 15, 125000.50,
    'web_upload', :'iid', 'reconciled'
);

-- pan_gstin_reconciliation_status accepts the new 'no_identifier' value.
INSERT INTO notices (
    tenant_id, matter_id, client_id, registration_id, law,
    ingest_channel, pan_gstin_reconciliation_status
) VALUES (
    :'tid', :'mid', :'cid', :'rid', 'IT',
    'web_upload', 'no_identifier'
);

-- Rejects unknown ingest_channel.
SELECT assert_raises(format($sql$
    INSERT INTO notices (tenant_id, matter_id, client_id, registration_id, law, ingest_channel)
    VALUES (%L, %L, %L, %L, 'IT', 'carrier_pigeon')
$sql$, :'tid', :'mid', :'cid', :'rid'), 'ingest_channel');

-- Rejects unknown reconciliation status.
SELECT assert_raises(format($sql$
    INSERT INTO notices (tenant_id, matter_id, client_id, registration_id, law,
                        ingest_channel, pan_gstin_reconciliation_status)
    VALUES (%L, %L, %L, %L, 'IT', 'web_upload', 'half_reconciled')
$sql$, :'tid', :'mid', :'cid', :'rid'), 'pan_gstin_reconciliation_status');
