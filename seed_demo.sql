-- ============================================================
-- NoticeDesk Demo Seed Data
-- Run: psql noticedesk_dev -U noticedesk_app -f seed_demo.sql
-- ============================================================
-- Fixed IDs for easy reference in headers / Postman:
--   Tenant:  11111111-1111-1111-1111-111111111111
--   User:    22222222-2222-2222-2222-222222222222
-- ============================================================

BEGIN;

-- ── Tenant: Sharma & Associates ─────────────────────────────
INSERT INTO tenants (tenant_id, legal_name, pricing_tier)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    'Sharma & Associates',
    'midsize'
) ON CONFLICT (tenant_id) DO NOTHING;

-- ── User (managing partner) ──────────────────────────────────
INSERT INTO users (user_id, tenant_id, name, role, email)
VALUES (
    '22222222-2222-2222-2222-222222222222',
    '11111111-1111-1111-1111-111111111111',
    'Rajesh Sharma',
    'managing_partner',
    'rajesh@sharmaassociates.in'
) ON CONFLICT DO NOTHING;

-- ═══════════════════════════════════════════════════════════
-- CLIENT 1: Acme Manufacturing Pvt Ltd
--   PAN: ABCDE1234F
--   GST: 27ABCDE1234F1Z5 (Maharashtra)
-- ═══════════════════════════════════════════════════════════
INSERT INTO clients (client_id, tenant_id, pan, legal_name, trade_name, entity_type, industry, email, phone)
VALUES (
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    '11111111-1111-1111-1111-111111111111',
    'ABCDE1234F',
    'Acme Manufacturing Pvt Ltd',
    'Acme Industries',
    'private_limited',
    'Manufacturing',
    'accounts@acme.in',
    '9876543210'
) ON CONFLICT (client_id) DO NOTHING;

-- IT registration
INSERT INTO client_registrations (registration_id, tenant_id, client_id, registration_type, identifier_value)
VALUES (
    'a1000000-0000-0000-0000-000000000001',
    '11111111-1111-1111-1111-111111111111',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'IT', 'ABCDE1234F'
) ON CONFLICT (registration_id) DO NOTHING;

-- GST registration (Maharashtra - state code 27)
INSERT INTO client_registrations (registration_id, tenant_id, client_id, registration_type, identifier_value, state_code, state_name, jurisdiction_office, registration_status)
VALUES (
    'a1000000-0000-0000-0000-000000000002',
    '11111111-1111-1111-1111-111111111111',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'GST', '27ABCDE1234F1Z5', '27', 'Maharashtra', 'Mumbai South', 'active'
) ON CONFLICT (registration_id) DO NOTHING;

-- ═══════════════════════════════════════════════════════════
-- CLIENT 2: Sunrise Traders LLP
--   PAN: PQRST5678K
--   GST: 29PQRST5678K1Z4 (Karnataka)
-- ═══════════════════════════════════════════════════════════
INSERT INTO clients (client_id, tenant_id, pan, legal_name, trade_name, entity_type, industry, email, phone)
VALUES (
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    '11111111-1111-1111-1111-111111111111',
    'PQRST5678K',
    'Sunrise Traders LLP',
    'Sunrise',
    'llp',
    'Trading',
    'finance@sunrise.in',
    '9123456789'
) ON CONFLICT (client_id) DO NOTHING;

INSERT INTO client_registrations (registration_id, tenant_id, client_id, registration_type, identifier_value)
VALUES (
    'b1000000-0000-0000-0000-000000000001',
    '11111111-1111-1111-1111-111111111111',
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    'IT', 'PQRST5678K'
) ON CONFLICT (registration_id) DO NOTHING;

INSERT INTO client_registrations (registration_id, tenant_id, client_id, registration_type, identifier_value, state_code, state_name, jurisdiction_office, registration_status)
VALUES (
    'b1000000-0000-0000-0000-000000000002',
    '11111111-1111-1111-1111-111111111111',
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    'GST', '29PQRST5678K1Z4', '29', 'Karnataka', 'Bengaluru North', 'active'
) ON CONFLICT (registration_id) DO NOTHING;

-- ═══════════════════════════════════════════════════════════
-- CLIENT 3: Veritas Consulting Pvt Ltd
--   PAN: MNOPQ9012R
--   GST: 07MNOPQ9012R1Z6 (Delhi)
-- ═══════════════════════════════════════════════════════════
INSERT INTO clients (client_id, tenant_id, pan, legal_name, trade_name, entity_type, industry, email, phone)
VALUES (
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    '11111111-1111-1111-1111-111111111111',
    'MNOPQ9012R',
    'Veritas Consulting Pvt Ltd',
    'Veritas',
    'private_limited',
    'Consulting',
    'tax@veritas.in',
    '9988776655'
) ON CONFLICT (client_id) DO NOTHING;

INSERT INTO client_registrations (registration_id, tenant_id, client_id, registration_type, identifier_value)
VALUES (
    'c1000000-0000-0000-0000-000000000001',
    '11111111-1111-1111-1111-111111111111',
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    'IT', 'MNOPQ9012R'
) ON CONFLICT (registration_id) DO NOTHING;

INSERT INTO client_registrations (registration_id, tenant_id, client_id, registration_type, identifier_value, state_code, state_name, jurisdiction_office, registration_status)
VALUES (
    'c1000000-0000-0000-0000-000000000002',
    '11111111-1111-1111-1111-111111111111',
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    'GST', '07MNOPQ9012R1Z6', '07', 'Delhi', 'Delhi Central', 'active'
) ON CONFLICT (registration_id) DO NOTHING;

-- ═══════════════════════════════════════════════════════════
-- MATTERS
-- ═══════════════════════════════════════════════════════════

-- Acme - GST matter FY 2022-23
INSERT INTO matters (matter_id, tenant_id, client_id, registration_id, law, financial_year, stage, status)
VALUES (
    'aa100000-0000-0000-0000-000000000001',
    '11111111-1111-1111-1111-111111111111',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'a1000000-0000-0000-0000-000000000002',
    'GST', '2022-23', 'notice', 'open'
) ON CONFLICT (matter_id) DO NOTHING;

-- Acme - IT matter AY 2023-24
INSERT INTO matters (matter_id, tenant_id, client_id, registration_id, law, assessment_year, stage, status)
VALUES (
    'aa100000-0000-0000-0000-000000000002',
    '11111111-1111-1111-1111-111111111111',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'a1000000-0000-0000-0000-000000000001',
    'IT', '2023-24', 'scrutiny', 'open'
) ON CONFLICT (matter_id) DO NOTHING;

-- Sunrise - GST matter FY 2023-24
INSERT INTO matters (matter_id, tenant_id, client_id, registration_id, law, financial_year, stage, status)
VALUES (
    'bb100000-0000-0000-0000-000000000001',
    '11111111-1111-1111-1111-111111111111',
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    'b1000000-0000-0000-0000-000000000002',
    'GST', '2023-24', 'notice', 'open'
) ON CONFLICT (matter_id) DO NOTHING;

-- Veritas - GST matter FY 2022-23
INSERT INTO matters (matter_id, tenant_id, client_id, registration_id, law, financial_year, stage, status)
VALUES (
    'cc100000-0000-0000-0000-000000000001',
    '11111111-1111-1111-1111-111111111111',
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    'c1000000-0000-0000-0000-000000000002',
    'GST', '2022-23', 'adjudication', 'open'
) ON CONFLICT (matter_id) DO NOTHING;

-- ═══════════════════════════════════════════════════════════
-- NOTICES
-- ═══════════════════════════════════════════════════════════

-- 1. Acme - GST SCN - DUE in 10 days (in_progress)
INSERT INTO notices (
    notice_id, tenant_id, matter_id, client_id, registration_id,
    law, document_type, din_or_rfn, issue_date, due_date,
    authority, financial_year, lifecycle_status, ingest_channel,
    demand_amount, issues
) VALUES (
    'ee000001-0000-0000-0000-000000000001',
    '11111111-1111-1111-1111-111111111111',
    'aa100000-0000-0000-0000-000000000001',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'a1000000-0000-0000-0000-000000000002',
    'GST', 'SCN', 'DIN/2024/SCN/00123',
    CURRENT_DATE - INTERVAL '15 days',
    CURRENT_DATE + INTERVAL '10 days',
    'CGST Mumbai South', '2022-23', 'in_progress', 'web_upload',
    450000,
    '["ITC mismatch under Section 16(4)", "Non-payment of GST on advances received"]'::jsonb
) ON CONFLICT (notice_id) DO NOTHING;

-- 2. Acme - GST DRC-01 - OVERDUE (due_date_over)
INSERT INTO notices (
    notice_id, tenant_id, matter_id, client_id, registration_id,
    law, document_type, din_or_rfn, issue_date, due_date,
    authority, financial_year, lifecycle_status, ingest_channel,
    demand_amount
) VALUES (
    'ee000001-0000-0000-0000-000000000002',
    '11111111-1111-1111-1111-111111111111',
    'aa100000-0000-0000-0000-000000000001',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'a1000000-0000-0000-0000-000000000002',
    'GST', 'DRC-01', 'DIN/2024/DRC/00456',
    CURRENT_DATE - INTERVAL '45 days',
    CURRENT_DATE - INTERVAL '5 days',
    'CGST Mumbai South', '2022-23', 'due_date_over', 'web_upload',
    128000
) ON CONFLICT (notice_id) DO NOTHING;

-- 3. Acme - IT Section 143(2) - hearing in 18 days (in_progress)
INSERT INTO notices (
    notice_id, tenant_id, matter_id, client_id, registration_id,
    law, document_type, din_or_rfn, issue_date, due_date, hearing_date,
    authority, assessment_year, lifecycle_status, ingest_channel,
    demand_amount
) VALUES (
    'ee000001-0000-0000-0000-000000000003',
    '11111111-1111-1111-1111-111111111111',
    'aa100000-0000-0000-0000-000000000002',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'a1000000-0000-0000-0000-000000000001',
    'IT', 'Section 143(2)', 'DIN/2024/IT/00789',
    CURRENT_DATE - INTERVAL '30 days',
    CURRENT_DATE + INTERVAL '20 days',
    CURRENT_DATE + INTERVAL '18 days',
    'ACIT Circle 5 Mumbai', '2023-24', 'in_progress', 'web_upload',
    320000
) ON CONFLICT (notice_id) DO NOTHING;

-- 4. Sunrise - GST ASMT-10 - freshly issued (issued)
INSERT INTO notices (
    notice_id, tenant_id, matter_id, client_id, registration_id,
    law, document_type, din_or_rfn, issue_date, due_date,
    authority, financial_year, lifecycle_status, ingest_channel,
    demand_amount, issues
) VALUES (
    'ee000002-0000-0000-0000-000000000001',
    '11111111-1111-1111-1111-111111111111',
    'bb100000-0000-0000-0000-000000000001',
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    'b1000000-0000-0000-0000-000000000002',
    'GST', 'ASMT-10', 'DIN/2024/ASMT/00234',
    CURRENT_DATE - INTERVAL '3 days',
    CURRENT_DATE + INTERVAL '27 days',
    'SGST Bengaluru North', '2023-24', 'issued', 'email',
    95000,
    '["Discrepancy in GSTR-1 vs GSTR-3B", "Excess ITC claimed in April 2023"]'::jsonb
) ON CONFLICT (notice_id) DO NOTHING;

-- 5. Veritas - GST SCN - reply already submitted
INSERT INTO notices (
    notice_id, tenant_id, matter_id, client_id, registration_id,
    law, document_type, din_or_rfn, issue_date, due_date,
    authority, financial_year, lifecycle_status, ingest_channel,
    demand_amount
) VALUES (
    'ee000003-0000-0000-0000-000000000001',
    '11111111-1111-1111-1111-111111111111',
    'cc100000-0000-0000-0000-000000000001',
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    'c1000000-0000-0000-0000-000000000002',
    'GST', 'SCN', 'DIN/2024/SCN/00567',
    CURRENT_DATE - INTERVAL '60 days',
    CURRENT_DATE - INTERVAL '15 days',
    'CGST Delhi Central', '2022-23', 'reply_submitted', 'web_upload',
    675000
) ON CONFLICT (notice_id) DO NOTHING;

-- 6. Veritas - GST order received (closed matter)
INSERT INTO notices (
    notice_id, tenant_id, matter_id, client_id, registration_id,
    law, document_type, din_or_rfn, issue_date, due_date,
    authority, financial_year, lifecycle_status, ingest_channel,
    demand_amount
) VALUES (
    'ee000003-0000-0000-0000-000000000002',
    '11111111-1111-1111-1111-111111111111',
    'cc100000-0000-0000-0000-000000000001',
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    'c1000000-0000-0000-0000-000000000002',
    'GST', 'OIO', 'DIN/2024/OIO/00091',
    CURRENT_DATE - INTERVAL '10 days',
    NULL,
    'CGST Delhi Central', '2022-23', 'order_received', 'web_upload',
    675000
) ON CONFLICT (notice_id) DO NOTHING;

COMMIT;

-- Quick summary
SELECT
    c.legal_name AS client,
    n.document_type,
    n.law,
    n.lifecycle_status,
    n.due_date,
    n.demand_amount
FROM notices n
JOIN clients c ON c.client_id = n.client_id
ORDER BY c.legal_name, n.due_date;
