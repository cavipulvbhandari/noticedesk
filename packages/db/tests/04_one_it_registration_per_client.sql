-- 04_one_it_registration_per_client.sql — partial unique index enforces exactly one IT row per client.
--
-- Note: the (tenant_id, identifier_value) UNIQUE constraint will catch the
-- second insert as well, since IT identifier_value MUST equal the client's
-- PAN, and the same PAN can't be re-inserted under the same tenant. Either
-- constraint firing is acceptable — both exist as defense in depth.

INSERT INTO tenants (legal_name) VALUES ('Test Firm') RETURNING tenant_id \gset

INSERT INTO clients (tenant_id, pan, legal_name)
VALUES (:'tenant_id', 'AAACX1234F', 'Acme Pvt Ltd')
RETURNING client_id \gset

-- First IT registration: succeeds.
SELECT assert_succeeds(format($sql$
    INSERT INTO client_registrations (tenant_id, client_id, registration_type, identifier_value)
    VALUES (%L, %L, 'IT', 'AAACX1234F')
$sql$, :'tenant_id', :'client_id'));

-- Second IT registration for the same client: blocked.
DO $$
DECLARE
    msg TEXT;
BEGIN
    BEGIN
        INSERT INTO client_registrations (tenant_id, client_id, registration_type, identifier_value)
        SELECT t.tenant_id, c.client_id, 'IT', 'AAACX1234F'
        FROM tenants t, clients c
        WHERE c.legal_name = 'Acme Pvt Ltd'
        LIMIT 1;
        RAISE EXCEPTION 'expected second IT registration to be blocked';
    EXCEPTION WHEN unique_violation THEN
        GET STACKED DIAGNOSTICS msg = MESSAGE_TEXT;
        IF msg NOT LIKE '%idx_one_it_reg_per_client%'
           AND msg NOT LIKE '%client_registrations_tenant_identifier_unique%' THEN
            RAISE EXCEPTION 'unexpected unique violation: %', msg;
        END IF;
    END;
END $$;

-- Multiple GST registrations for the same client are permitted.
SELECT assert_succeeds(format($sql$
    INSERT INTO client_registrations (tenant_id, client_id, registration_type, identifier_value, state_code, state_name)
    VALUES (%L, %L, 'GST', '27AAACX1234F1Z5', '27', 'Maharashtra')
$sql$, :'tenant_id', :'client_id'));

SELECT assert_succeeds(format($sql$
    INSERT INTO client_registrations (tenant_id, client_id, registration_type, identifier_value, state_code, state_name)
    VALUES (%L, %L, 'GST', '24AAACX1234F1Z3', '24', 'Gujarat')
$sql$, :'tenant_id', :'client_id'));
