-- phase1_demo.sql
-- Sprint 1 minimum demo seed: one tenant + one managing partner.
-- Sprint 3 expands this to the full prototype fixture set (5 clients,
-- 14 registrations, 39 notices). Idempotent: safe to re-run.

INSERT INTO tenants (
    tenant_id, legal_name, address, jurisdiction, pricing_tier, partner_count
) VALUES (
    '11111111-1111-1111-1111-111111111111',
    'Mehta & Associates',
    'Fort, Mumbai',
    'Maharashtra',
    'midsize',
    4
)
ON CONFLICT (tenant_id) DO NOTHING;

INSERT INTO users (
    user_id, tenant_id, name, role, email, mfa_enabled
) VALUES (
    '22222222-2222-2222-2222-222222222222',
    '11111111-1111-1111-1111-111111111111',
    'CA Rohan Mehta',
    'managing_partner',
    'rohan@mehta-associates.example',
    FALSE
)
ON CONFLICT (user_id) DO NOTHING;
