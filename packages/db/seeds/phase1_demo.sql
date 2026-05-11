-- phase1_demo.sql
-- Sprint 3 demo seed: minimal coverage for the inbox routing flow.
--
-- - 1 demo tenant + 1 user
-- - 2 clients with full registration setups, mirroring the prototype's
--   Acme & Cinnamon firms.
-- - 3 pre-seeded inbox rows (i1, i2, i3) covering the three routing
--   decisions the acceptance criteria call out.
--
-- Runs as superuser; tenant context is set inside the file so RLS doesn't
-- block the inserts. Idempotent: re-running upserts rather than failing on
-- duplicate slugs.

BEGIN;

-- ---- Tenant + user --------------------------------------------------------

INSERT INTO tenants (tenant_id, legal_name, slug)
VALUES ('11111111-1111-1111-1111-111111111111', 'Mehta & Associates', 'mehta-associates')
ON CONFLICT (tenant_id) DO UPDATE SET legal_name = EXCLUDED.legal_name;

INSERT INTO users (user_id, tenant_id, name, role, email)
VALUES (
    '22222222-2222-2222-2222-222222222222',
    '11111111-1111-1111-1111-111111111111',
    'Demo Partner', 'partner', 'demo@example.com'
) ON CONFLICT (user_id) DO NOTHING;

SELECT set_config('app.current_tenant', '11111111-1111-1111-1111-111111111111', true);

-- ---- Client 1 — Acme Industries Private Limited ---------------------------

INSERT INTO clients (client_id, tenant_id, pan, legal_name, trade_name, entity_type)
VALUES (
    'aaaaaaaa-1111-1111-1111-111111111111',
    '11111111-1111-1111-1111-111111111111',
    'AAACA9876B', 'Acme Industries Private Limited', 'Acme Industries', 'company'
) ON CONFLICT (client_id) DO NOTHING;

INSERT INTO client_registrations (
    registration_id, tenant_id, client_id, registration_type, identifier_value
) VALUES (
    'aaaaaaaa-2222-2222-2222-111111111111',
    '11111111-1111-1111-1111-111111111111',
    'aaaaaaaa-1111-1111-1111-111111111111',
    'IT', 'AAACA9876B'
) ON CONFLICT (registration_id) DO NOTHING;

INSERT INTO client_registrations (
    registration_id, tenant_id, client_id, registration_type,
    identifier_value, state_code, state_name, registration_status
) VALUES
    (
      'aaaaaaaa-3333-3333-3333-111111111111',
      '11111111-1111-1111-1111-111111111111',
      'aaaaaaaa-1111-1111-1111-111111111111',
      'GST', '27AAACA9876B1Z5', '27', 'Maharashtra', 'active'
    ),
    (
      'aaaaaaaa-3333-3333-3333-222222222222',
      '11111111-1111-1111-1111-111111111111',
      'aaaaaaaa-1111-1111-1111-111111111111',
      'GST', '24AAACA9876B1Z3', '24', 'Gujarat', 'active'
    )
ON CONFLICT (registration_id) DO NOTHING;

-- ---- Client 2 — Cinnamon Bakery LLP ---------------------------------------

INSERT INTO clients (client_id, tenant_id, pan, legal_name, entity_type)
VALUES (
    'cccccccc-1111-1111-1111-111111111111',
    '11111111-1111-1111-1111-111111111111',
    'AAACC2345D', 'Cinnamon Bakery LLP', 'LLP'
) ON CONFLICT (client_id) DO NOTHING;

INSERT INTO client_registrations (
    registration_id, tenant_id, client_id, registration_type, identifier_value
) VALUES (
    'cccccccc-2222-2222-2222-111111111111',
    '11111111-1111-1111-1111-111111111111',
    'cccccccc-1111-1111-1111-111111111111',
    'IT', 'AAACC2345D'
) ON CONFLICT (registration_id) DO NOTHING;

INSERT INTO client_registrations (
    registration_id, tenant_id, client_id, registration_type,
    identifier_value, state_code, state_name, registration_status
) VALUES (
    'cccccccc-3333-3333-3333-111111111111',
    '11111111-1111-1111-1111-111111111111',
    'cccccccc-1111-1111-1111-111111111111',
    'GST', '07AAACC2345D1Z9', '07', 'Delhi', 'active'
) ON CONFLICT (registration_id) DO NOTHING;

-- ---- i1: routed cleanly to Acme Maharashtra GST ---------------------------

INSERT INTO documents_inbox (
    inbox_id, tenant_id, original_filename, file_hash, file_size_bytes,
    mime_type, s3_key, ingest_channel,
    ocr_status, ocr_text, ocr_provider_used, page_count, ocr_completed_at,
    parse_status, routing_status,
    raw_parsed_json
) VALUES (
    '00000000-0000-0000-0000-00000000000a',
    '11111111-1111-1111-1111-111111111111',
    'ASMT-10_27AAACA9876B1Z5.pdf',
    '1111111111111111111111111111111111111111111111111111111111111111',
    98765, 'application/pdf',
    'seed/i1.pdf', 'email',
    'completed',
    'NOTICE OF ASMT-10 to Acme Industries GSTIN 27AAACA9876B1Z5 for FY 2022-23 ...',
    'stub', 3, NOW(),
    'completed', 'pending',  -- routing_status reset to 'pending' so the seed
                              -- re-routes deterministically when the API is
                              -- restarted; the manual INSERT below sets it
                              -- to 'routed' explicitly.
    '{"document_type":"ASMT-10","law":"GST","client_name_on_document":"Acme Industries Private Limited","pans_extracted":[],"gstins_extracted":[{"value":"27AAACA9876B1Z5","location":"para 1","state_code":"27"}],"notice_number":"ASMT-10/2024/0001","issue_date":"2024-09-12","due_date":"2024-09-30","financial_year":"2022-23","assessment_year":null,"authority":"State Tax Officer, Mumbai Ward 5","issues":["ITC mismatch with 2A"],"documents_required":["GSTR-3B for 2022-23","Purchase register"],"parse_confidence":0.92,"fields_needing_review":[]}'::JSONB
) ON CONFLICT (inbox_id) DO NOTHING;

-- ---- i2: client_not_found (PAN extracted but no matching client) ----------

INSERT INTO documents_inbox (
    inbox_id, tenant_id, original_filename, file_hash, file_size_bytes,
    mime_type, s3_key, ingest_channel,
    ocr_status, ocr_text, ocr_provider_used, page_count, ocr_completed_at,
    parse_status, routing_status,
    raw_parsed_json, routing_anomaly_details
) VALUES (
    '00000000-0000-0000-0000-00000000000b',
    '11111111-1111-1111-1111-111111111111',
    'DRC-01A_27AAQCS3456P1ZF.pdf',
    '2222222222222222222222222222222222222222222222222222222222222222',
    54321, 'application/pdf',
    'seed/i2.pdf', 'web_upload',
    'completed',
    'INTIMATION DRC-01A to SUNRISE PAPERS PVT LTD GSTIN 27AAQCS3456P1ZF for FY 2023-24 ...',
    'stub', 2, NOW(),
    'completed', 'client_not_found',
    '{"document_type":"DRC-01A","law":"GST","client_name_on_document":"Sunrise Papers Pvt Ltd","pans_extracted":[],"gstins_extracted":[{"value":"27AAQCS3456P1ZF","location":"header","state_code":"27"}],"financial_year":"2023-24","authority":"State Tax Officer, Pune Range","issues":["Short payment of tax under section 73"],"documents_required":["Reply on DRC-01A within 7 days"],"parse_confidence":0.88,"fields_needing_review":[]}'::JSONB,
    '{"canonical_pan":"AAQCS3456P","extracted_name":"Sunrise Papers Pvt Ltd","extracted_gstins":["27AAQCS3456P1ZF"]}'::JSONB
) ON CONFLICT (inbox_id) DO NOTHING;

-- ---- i3: new_gst_registration_detected (Acme PAN matches; new state GSTIN) -

INSERT INTO documents_inbox (
    inbox_id, tenant_id, original_filename, file_hash, file_size_bytes,
    mime_type, s3_key, ingest_channel,
    ocr_status, ocr_text, ocr_provider_used, page_count, ocr_completed_at,
    parse_status, routing_status,
    raw_parsed_json, routing_anomaly_details
) VALUES (
    '00000000-0000-0000-0000-00000000000c',
    '11111111-1111-1111-1111-111111111111',
    'ASMT-10_29AAACA9876B1ZK.pdf',
    '3333333333333333333333333333333333333333333333333333333333333333',
    76543, 'application/pdf',
    'seed/i3.pdf', 'web_upload',
    'completed',
    'NOTICE OF ASMT-10 to Acme Industries GSTIN 29AAACA9876B1ZK (Karnataka) for FY 2023-24 ...',
    'stub', 2, NOW(),
    'completed', 'new_gst_registration_detected',
    '{"document_type":"ASMT-10","law":"GST","client_name_on_document":"Acme Industries Private Limited","pans_extracted":[],"gstins_extracted":[{"value":"29AAACA9876B1ZK","location":"header","state_code":"29"}],"financial_year":"2023-24","issues":["ITC mismatch"],"documents_required":[],"parse_confidence":0.90,"fields_needing_review":[]}'::JSONB,
    ('{"canonical_pan":"AAACA9876B","client_id":"aaaaaaaa-1111-1111-1111-111111111111","client_legal_name":"Acme Industries Private Limited","gstin":"29AAACA9876B1ZK","state_code":"29"}')::JSONB
) ON CONFLICT (inbox_id) DO NOTHING;

-- Manually route i1 to keep the demo state deterministic.

DO $$
DECLARE
    v_inbox UUID := '00000000-0000-0000-0000-00000000000a';
    v_client UUID := 'aaaaaaaa-1111-1111-1111-111111111111';
    v_reg UUID := 'aaaaaaaa-3333-3333-3333-111111111111';
    v_tenant UUID := '11111111-1111-1111-1111-111111111111';
    v_matter UUID;
    v_notice UUID;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM notices WHERE source_inbox_id = v_inbox) THEN
        INSERT INTO matters (tenant_id, client_id, registration_id, law, financial_year)
        VALUES (v_tenant, v_client, v_reg, 'GST', '2022-23')
        RETURNING matter_id INTO v_matter;

        INSERT INTO notices (
            tenant_id, matter_id, client_id, registration_id, law,
            document_type, notice_number, issue_date, due_date, authority,
            financial_year, ingest_channel, source_inbox_id,
            parse_confidence, pan_gstin_reconciliation_status,
            raw_extracted_json
        ) VALUES (
            v_tenant, v_matter, v_client, v_reg, 'GST',
            'ASMT-10', 'ASMT-10/2024/0001', DATE '2024-09-12', DATE '2024-09-30',
            'State Tax Officer, Mumbai Ward 5', '2022-23',
            'email', v_inbox, 0.92, 'reconciled',
            '{"issues":["ITC mismatch with 2A"]}'::JSONB
        ) RETURNING notice_id INTO v_notice;

        UPDATE documents_inbox
        SET routing_status = 'routed',
            parsed_to_notice_id = v_notice
        WHERE inbox_id = v_inbox;
    END IF;
END $$;

COMMIT;
