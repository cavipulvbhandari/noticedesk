-- 0007_cross_adjudication_flags.sql
-- The PAN linkage between GST and IT runs through client_id.

CREATE TABLE IF NOT EXISTS cross_adjudication_flags (
    flag_id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                 UUID NOT NULL REFERENCES tenants (tenant_id) ON DELETE RESTRICT,
    matter_id                 UUID NOT NULL REFERENCES matters (matter_id) ON DELETE RESTRICT,
    client_id                 UUID NOT NULL REFERENCES clients (client_id) ON DELETE RESTRICT,
    source_law                TEXT CHECK (source_law IN ('GST', 'IT')),
    impacted_law              TEXT CHECK (impacted_law IN ('GST', 'IT')),
    source_registration_id    UUID REFERENCES client_registrations (registration_id),
    impacted_registration_ids UUID[],
    trigger_pattern           TEXT CHECK (trigger_pattern IN ('A', 'B', 'C', 'D', 'E', 'F')),
    factual_link              TEXT,
    draft_admission_risk      TEXT CHECK (draft_admission_risk IN ('none', 'low', 'moderate', 'high')),
    suggested_phrasing_change TEXT,
    partner_dismissed         BOOLEAN NOT NULL DEFAULT FALSE,
    partner_dismissal_reason  TEXT,
    created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_cross_flags_client ON cross_adjudication_flags (client_id);
CREATE INDEX IF NOT EXISTS idx_cross_flags_matter ON cross_adjudication_flags (matter_id);
