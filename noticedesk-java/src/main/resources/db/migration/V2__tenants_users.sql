-- 0002_tenants_users.sql
-- Tenants (firms) and users.

CREATE TABLE IF NOT EXISTS tenants (
    tenant_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    legal_name             TEXT NOT NULL,
    gstin                  TEXT,
    pan                    TEXT,
    address                TEXT,
    jurisdiction           TEXT,
    pricing_tier           TEXT CHECK (pricing_tier IN ('solo', 'midsize', 'boutique', 'enterprise')),
    annual_prepaid_until   DATE,
    partner_count          INT,
    staff_count            INT,
    delegation_matrix      JSONB,
    dpdp_consent_record    JSONB,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users (
    user_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id        UUID NOT NULL REFERENCES tenants (tenant_id) ON DELETE RESTRICT,
    name             TEXT NOT NULL,
    role             TEXT NOT NULL CHECK (role IN ('partner', 'managing_partner', 'manager', 'staff', 'client')),
    phone            TEXT,
    email            CITEXT,
    whatsapp_opt_in  BOOLEAN NOT NULL DEFAULT FALSE,
    last_login       TIMESTAMPTZ,
    mfa_enabled      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_tenant ON users (tenant_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_tenant_email ON users (tenant_id, email) WHERE email IS NOT NULL;
