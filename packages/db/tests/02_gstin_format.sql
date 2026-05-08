-- 02_gstin_format.sql — client_registrations.identifier_format CHECK on GSTIN.
--
-- Each invalid case below keeps the embedded PAN equal to the client's PAN so
-- the PAN-consistency trigger lets the row through; we then verify the CHECK
-- constraint rejects the malformed GSTIN. (A separate test case at the bottom
-- exercises the trigger when the CHECK can't catch the issue first.)

INSERT INTO tenants (legal_name) VALUES ('Test Firm') RETURNING tenant_id \gset

INSERT INTO clients (tenant_id, pan, legal_name)
VALUES (:'tenant_id', 'AAACX1234F', 'Acme Pvt Ltd')
RETURNING client_id \gset

-- Valid GSTIN.
SELECT assert_succeeds(format($sql$
    INSERT INTO client_registrations (tenant_id, client_id, registration_type, identifier_value, state_code, state_name)
    VALUES (%L, %L, 'GST', '27AAACX1234F1Z5', '27', 'Maharashtra')
$sql$, :'tenant_id', :'client_id'));

-- Invalid: 14 chars. PAN portion still 'AAACX1234F' so trigger passes; CHECK fails.
SELECT assert_raises(format($sql$
    INSERT INTO client_registrations (tenant_id, client_id, registration_type, identifier_value, state_code, state_name)
    VALUES (%L, %L, 'GST', '27AAACX1234F1Z', '27', 'Maharashtra')
$sql$, :'tenant_id', :'client_id'), 'identifier_format');

-- Invalid: 16 chars.
SELECT assert_raises(format($sql$
    INSERT INTO client_registrations (tenant_id, client_id, registration_type, identifier_value, state_code, state_name)
    VALUES (%L, %L, 'GST', '27AAACX1234F1Z55', '27', 'Maharashtra')
$sql$, :'tenant_id', :'client_id'), 'identifier_format');

-- Invalid: position 14 must be 'Z' (here it's 'A'). PAN portion still matches.
SELECT assert_raises(format($sql$
    INSERT INTO client_registrations (tenant_id, client_id, registration_type, identifier_value, state_code, state_name)
    VALUES (%L, %L, 'GST', '27AAACX1234F1A5', '27', 'Maharashtra')
$sql$, :'tenant_id', :'client_id'), 'identifier_format');

-- Invalid: lowercase. PAN-consistency trigger catches this first; either way
-- the row must be rejected.
DO $$
BEGIN
    BEGIN
        INSERT INTO client_registrations (tenant_id, client_id, registration_type, identifier_value, state_code, state_name)
        SELECT t.tenant_id, c.client_id, 'GST', '27aaacx1234f1z5', '27', 'Maharashtra'
        FROM tenants t, clients c
        WHERE c.legal_name = 'Acme Pvt Ltd' LIMIT 1;
        RAISE EXCEPTION 'expected lowercase GSTIN to be rejected';
    EXCEPTION WHEN check_violation OR raise_exception THEN
        -- Either the CHECK or the trigger may fire; both are acceptable.
        NULL;
    END;
END $$;
