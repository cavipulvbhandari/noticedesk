-- 0003_clients_registrations.sql
-- Clients (PAN-keyed) and their IT/GST registrations.
--
-- Identity model invariants enforced by this migration:
--   1. PAN matches ^[A-Z]{5}[0-9]{4}[A-Z]$
--   2. GSTIN matches ^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]$
--   3. IT registration: identifier_value == client.pan (trigger)
--   4. GST registration: identifier_value[3:12] == client.pan (trigger)
--   5. Exactly one IT registration per client (partial unique index)
--   6. Each (tenant, identifier_value) globally unique within the firm

CREATE TABLE IF NOT EXISTS clients (
    client_id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                       UUID NOT NULL REFERENCES tenants (tenant_id) ON DELETE RESTRICT,
    pan                             TEXT NOT NULL,
    legal_name                      TEXT NOT NULL,
    trade_name                      TEXT,
    entity_type                     TEXT,
    cin                             TEXT,
    date_of_incorporation_or_birth  DATE,
    primary_contact_user_id         UUID REFERENCES users (user_id),
    industry                        TEXT,
    group_relationships             JSONB,
    billing_profile                 JSONB,
    created_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT pan_format CHECK (pan ~ '^[A-Z]{5}[0-9]{4}[A-Z]$'),
    CONSTRAINT clients_tenant_pan_unique UNIQUE (tenant_id, pan)
);

CREATE INDEX IF NOT EXISTS idx_clients_tenant_pan ON clients (tenant_id, pan);
CREATE INDEX IF NOT EXISTS idx_clients_tenant_legal_name ON clients (tenant_id, legal_name);

CREATE TABLE IF NOT EXISTS client_registrations (
    registration_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id            UUID NOT NULL REFERENCES tenants (tenant_id) ON DELETE RESTRICT,
    client_id            UUID NOT NULL REFERENCES clients (client_id) ON DELETE RESTRICT,
    registration_type    TEXT NOT NULL CHECK (registration_type IN ('IT', 'GST')),
    identifier_value     TEXT NOT NULL,
    state_code           TEXT,
    state_name           TEXT,
    jurisdiction_office  TEXT,
    registration_status  TEXT CHECK (registration_status IN ('active', 'suspended', 'cancelled', 'surrendered')),
    effective_from       DATE,
    effective_to         DATE,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Format check: IT identifier is PAN (10 chars), GST identifier is GSTIN (15 chars).
    CONSTRAINT identifier_format CHECK (
        (registration_type = 'IT'  AND identifier_value ~ '^[A-Z]{5}[0-9]{4}[A-Z]$')
        OR
        (registration_type = 'GST' AND identifier_value ~ '^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]$')
    ),

    -- IT must not have state_code; GST must have a 2-digit state_code.
    CONSTRAINT state_code_consistency CHECK (
        (registration_type = 'IT'  AND state_code IS NULL)
        OR
        (registration_type = 'GST' AND state_code ~ '^[0-9]{2}$')
    ),

    CONSTRAINT client_registrations_tenant_identifier_unique UNIQUE (tenant_id, identifier_value)
);

CREATE INDEX IF NOT EXISTS idx_client_reg_client ON client_registrations (client_id);
CREATE INDEX IF NOT EXISTS idx_client_reg_type_state ON client_registrations (client_id, registration_type, state_code);

-- Exactly one IT registration per client.
CREATE UNIQUE INDEX IF NOT EXISTS idx_one_it_reg_per_client
    ON client_registrations (client_id)
    WHERE registration_type = 'IT';

-- Trigger: enforce PAN consistency between client and registration.
CREATE OR REPLACE FUNCTION enforce_registration_pan_consistency()
RETURNS TRIGGER AS $$
DECLARE
    client_pan TEXT;
    gstin_pan  TEXT;
BEGIN
    SELECT pan INTO client_pan FROM clients WHERE client_id = NEW.client_id;
    IF client_pan IS NULL THEN
        RAISE EXCEPTION 'client_id % does not exist or has no PAN', NEW.client_id;
    END IF;

    IF NEW.registration_type = 'IT' THEN
        IF NEW.identifier_value <> client_pan THEN
            RAISE EXCEPTION 'IT registration identifier_value (%) must equal client PAN (%)',
                NEW.identifier_value, client_pan;
        END IF;
    ELSIF NEW.registration_type = 'GST' THEN
        gstin_pan := SUBSTRING(NEW.identifier_value FROM 3 FOR 10);
        IF gstin_pan <> client_pan THEN
            RAISE EXCEPTION
                'GST registration identifier_value (%) positions 3-12 must equal client PAN (%). Got positions 3-12 = %',
                NEW.identifier_value, client_pan, gstin_pan;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_registration_pan_consistency ON client_registrations;
CREATE TRIGGER trg_registration_pan_consistency
    BEFORE INSERT OR UPDATE ON client_registrations
    FOR EACH ROW EXECUTE FUNCTION enforce_registration_pan_consistency();
