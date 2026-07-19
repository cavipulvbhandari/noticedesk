-- 0004_matters_notices.sql
-- Matters and notices. Both must resolve to (client_id, registration_id).

CREATE TABLE IF NOT EXISTS matters (
    matter_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id          UUID NOT NULL REFERENCES tenants (tenant_id) ON DELETE RESTRICT,
    client_id          UUID NOT NULL REFERENCES clients (client_id) ON DELETE RESTRICT,
    registration_id    UUID NOT NULL REFERENCES client_registrations (registration_id) ON DELETE RESTRICT,
    law                TEXT NOT NULL CHECK (law IN ('GST', 'IT')),
    forum              TEXT,
    stage              TEXT,
    status             TEXT,
    financial_year     TEXT,
    assessment_year    TEXT,
    opening_date       DATE,
    closing_date       DATE,
    partner_owner_id   UUID REFERENCES users (user_id),
    manager_id         UUID REFERENCES users (user_id),
    staff_ids          UUID[],
    demand_quantum     NUMERIC,
    limitation_dates   JSONB,
    pre_deposit_status JSONB,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_matters_client       ON matters (client_id);
CREATE INDEX IF NOT EXISTS idx_matters_registration ON matters (registration_id);
CREATE INDEX IF NOT EXISTS idx_matters_law_year     ON matters (law, financial_year, assessment_year);

-- Trigger: enforce matters.law matches the registration's type.
CREATE OR REPLACE FUNCTION enforce_matter_registration_law()
RETURNS TRIGGER AS $$
DECLARE
    reg_type      TEXT;
    reg_client_id UUID;
BEGIN
    SELECT registration_type, client_id
        INTO reg_type, reg_client_id
        FROM client_registrations
        WHERE registration_id = NEW.registration_id;

    IF reg_type IS NULL THEN
        RAISE EXCEPTION 'registration_id % does not exist', NEW.registration_id;
    END IF;

    IF reg_type <> NEW.law THEN
        RAISE EXCEPTION 'matters.law (%) must match the registration_type of registration_id (%)',
            NEW.law, reg_type;
    END IF;

    IF reg_client_id <> NEW.client_id THEN
        RAISE EXCEPTION 'matters.client_id (%) must equal client_registrations.client_id (%) for registration_id %',
            NEW.client_id, reg_client_id, NEW.registration_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_matter_registration_law ON matters;
CREATE TRIGGER trg_matter_registration_law
    BEFORE INSERT OR UPDATE ON matters
    FOR EACH ROW EXECUTE FUNCTION enforce_matter_registration_law();

-- Notices.
CREATE TABLE IF NOT EXISTS notices (
    notice_id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                       UUID NOT NULL REFERENCES tenants (tenant_id) ON DELETE RESTRICT,
    matter_id                       UUID NOT NULL REFERENCES matters (matter_id) ON DELETE RESTRICT,
    client_id                       UUID NOT NULL REFERENCES clients (client_id) ON DELETE RESTRICT,
    registration_id                 UUID NOT NULL REFERENCES client_registrations (registration_id) ON DELETE RESTRICT,
    law                             TEXT NOT NULL CHECK (law IN ('GST', 'IT')),
    document_type                   TEXT,
    notice_number                   TEXT,
    din_or_rfn                      TEXT,
    issue_date                      DATE,
    receipt_date                    DATE,
    due_date                        DATE,
    due_time                        TIME,
    authority                       TEXT,
    financial_year                  TEXT,
    assessment_year                 TEXT,
    issues                          JSONB,
    documents_required              JSONB,
    hearing_date                    DATE,
    lifecycle_status                TEXT NOT NULL DEFAULT 'issued' CHECK (lifecycle_status IN (
        'issued',
        'in_progress',
        'due',
        'due_date_over',
        'reply_submitted',
        'acknowledged',
        'order_received',
        'appeal_filed',
        'closed',
        'on_hold'
    )),
    source_file_hash                TEXT,
    parse_confidence                NUMERIC,
    verification_status             TEXT,
    pan_gstin_reconciliation_status TEXT CHECK (pan_gstin_reconciliation_status IN (
        'reconciled',
        'pending',
        'mismatch_blocked'
    )),
    raw_extracted_json              JSONB,
    manual_corrections_json         JSONB,
    created_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notices_client       ON notices (client_id);
CREATE INDEX IF NOT EXISTS idx_notices_registration ON notices (registration_id);
CREATE INDEX IF NOT EXISTS idx_notices_status       ON notices (tenant_id, lifecycle_status);
CREATE INDEX IF NOT EXISTS idx_notices_due_date     ON notices (tenant_id, due_date)
    WHERE lifecycle_status IN ('issued', 'in_progress', 'due', 'due_date_over');
CREATE INDEX IF NOT EXISTS idx_notices_law_fy
    ON notices (registration_id, law, financial_year, assessment_year);

-- Trigger: notices must be consistent with their parent matter and registration.
CREATE OR REPLACE FUNCTION enforce_notice_consistency()
RETURNS TRIGGER AS $$
DECLARE
    matter_client_id       UUID;
    matter_registration_id UUID;
    matter_law             TEXT;
    matter_tenant_id       UUID;
BEGIN
    SELECT client_id, registration_id, law, tenant_id
        INTO matter_client_id, matter_registration_id, matter_law, matter_tenant_id
        FROM matters
        WHERE matter_id = NEW.matter_id;

    IF matter_client_id IS NULL THEN
        RAISE EXCEPTION 'matter_id % does not exist', NEW.matter_id;
    END IF;

    IF NEW.client_id <> matter_client_id THEN
        RAISE EXCEPTION 'notice client_id (%) must equal matter client_id (%)',
            NEW.client_id, matter_client_id;
    END IF;

    IF NEW.registration_id <> matter_registration_id THEN
        RAISE EXCEPTION 'notice registration_id (%) must equal matter registration_id (%)',
            NEW.registration_id, matter_registration_id;
    END IF;

    IF NEW.law <> matter_law THEN
        RAISE EXCEPTION 'notice law (%) must equal matter law (%)', NEW.law, matter_law;
    END IF;

    IF NEW.tenant_id <> matter_tenant_id THEN
        RAISE EXCEPTION 'notice tenant_id (%) must equal matter tenant_id (%)',
            NEW.tenant_id, matter_tenant_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_notice_consistency ON notices;
CREATE TRIGGER trg_notice_consistency
    BEFORE INSERT OR UPDATE ON notices
    FOR EACH ROW EXECUTE FUNCTION enforce_notice_consistency();
