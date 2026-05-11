-- 09_documents_inbox.sql — schema invariants on documents_inbox.
--
-- Mirrors the role-switch pattern in 07_tenant_isolation.sql so that RLS is
-- actually enforced (FORCE ROW LEVEL SECURITY applies to table owners but
-- not to superusers). The ``noticedesk_app`` role is created by migration
-- 0012.

INSERT INTO tenants (legal_name) VALUES ('Acme Firm') RETURNING tenant_id AS tenant_a \gset
INSERT INTO tenants (legal_name) VALUES ('Other Firm') RETURNING tenant_id AS tenant_b \gset

SET LOCAL ROLE noticedesk_app;
SELECT set_config('app.current_tenant', :'tenant_a', true);

-- Valid insert: tenant_a context, tenant_a row. We deliberately pin the
-- file_hash so the touch-test below can look the row back up by hash.
INSERT INTO documents_inbox (
    tenant_id, original_filename, file_hash, file_size_bytes,
    s3_key, mime_type, ingest_channel
) VALUES (
    :'tenant_a', 'asmt-10.pdf',
    'abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789',
    102400, 'tenants/x/inbox/y/asmt-10.pdf', 'application/pdf', 'web_upload'
);

-- file_hash must be hex64.
SELECT assert_raises(format($sql$
    INSERT INTO documents_inbox (tenant_id, original_filename, file_hash, file_size_bytes, s3_key, ingest_channel)
    VALUES (%L, 'x.pdf', 'not-a-hash', 1, 'k', 'web_upload')
$sql$, :'tenant_a'), 'file_hash_format');

-- file_size_bytes must be positive.
SELECT assert_raises(format($sql$
    INSERT INTO documents_inbox (tenant_id, original_filename, file_hash, file_size_bytes, s3_key, ingest_channel)
    VALUES (%L, 'x.pdf', repeat('a', 64), 0, 'k', 'web_upload')
$sql$, :'tenant_a'), 'file_size_positive');

-- ocr_status must be one of the allowed values.
SELECT assert_raises(format($sql$
    INSERT INTO documents_inbox (tenant_id, original_filename, file_hash, file_size_bytes, s3_key, ingest_channel, ocr_status)
    VALUES (%L, 'x.pdf', repeat('a', 64), 1, 'k', 'web_upload', 'banana')
$sql$, :'tenant_a'), 'ocr_status');

-- ingest_channel must be one of the six values.
SELECT assert_raises(format($sql$
    INSERT INTO documents_inbox (tenant_id, original_filename, file_hash, file_size_bytes, s3_key, ingest_channel)
    VALUES (%L, 'x.pdf', repeat('a', 64), 1, 'k', 'fax_machine')
$sql$, :'tenant_a'), 'ingest_channel');

-- All six valid ingest_channel values are accepted.
DO $$
DECLARE
    chans TEXT[] := ARRAY[
        'web_upload', 'mobile_capture', 'email',
        'gst_portal_gsp', 'it_portal_aa', 'whatsapp'
    ];
    chan TEXT;
    tid UUID;
BEGIN
    tid := current_tenant_id();
    FOREACH chan IN ARRAY chans LOOP
        INSERT INTO documents_inbox (
            tenant_id, original_filename, file_hash, file_size_bytes,
            s3_key, ingest_channel
        ) VALUES (
            tid, 'x.pdf', repeat('a', 64), 1,
            'k-' || chan, chan
        );
    END LOOP;
END $$;

-- updated_at is auto-touched on UPDATE.
DO $$
DECLARE
    target UUID;
    before_ts TIMESTAMPTZ;
    after_ts  TIMESTAMPTZ;
BEGIN
    SELECT inbox_id, updated_at INTO target, before_ts
        FROM documents_inbox WHERE original_filename = 'asmt-10.pdf';
    PERFORM pg_sleep(0.05);
    UPDATE documents_inbox SET ocr_status = 'in_progress' WHERE inbox_id = target;
    SELECT updated_at INTO after_ts FROM documents_inbox WHERE inbox_id = target;
    IF after_ts <= before_ts THEN
        RAISE EXCEPTION 'updated_at not auto-touched: before=%, after=%', before_ts, after_ts;
    END IF;
END $$;

-- RLS: switching to tenant_b context hides tenant_a's rows.
SELECT set_config('app.current_tenant', :'tenant_b', true);
DO $$
DECLARE
    cnt INT;
BEGIN
    SELECT COUNT(*) INTO cnt FROM documents_inbox;
    IF cnt <> 0 THEN
        RAISE EXCEPTION 'expected 0 inbox rows visible to tenant_b, got %', cnt;
    END IF;
END $$;

-- And tenant_b cannot insert a row claiming to belong to tenant_a.
SELECT assert_raises(format($sql$
    INSERT INTO documents_inbox (tenant_id, original_filename, file_hash, file_size_bytes, s3_key, ingest_channel)
    VALUES (%L, 'x.pdf', repeat('a', 64), 1, 'k', 'web_upload')
$sql$, :'tenant_a'), 'row-level security');

RESET ROLE;
