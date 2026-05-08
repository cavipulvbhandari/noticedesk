-- 03_registration_pan_consistency.sql — trigger enforces PAN match between client and registration.

INSERT INTO tenants (legal_name) VALUES ('Test Firm') RETURNING tenant_id \gset

INSERT INTO clients (tenant_id, pan, legal_name)
VALUES (:'tenant_id', 'AAACX1234F', 'Acme Pvt Ltd')
RETURNING client_id \gset

-- IT registration with matching PAN: succeeds.
SELECT assert_succeeds(format($sql$
    INSERT INTO client_registrations (tenant_id, client_id, registration_type, identifier_value)
    VALUES (%L, %L, 'IT', 'AAACX1234F')
$sql$, :'tenant_id', :'client_id'));

-- IT registration with a different PAN: trigger blocks.
SELECT assert_raises(format($sql$
    INSERT INTO client_registrations (tenant_id, client_id, registration_type, identifier_value)
    VALUES (%L, %L, 'IT', 'BBBCX1234F')
$sql$, :'tenant_id', :'client_id'), 'must equal client PAN');

-- GST whose positions 3-12 match the PAN: succeeds (Karnataka).
SELECT assert_succeeds(format($sql$
    INSERT INTO client_registrations (tenant_id, client_id, registration_type, identifier_value, state_code, state_name)
    VALUES (%L, %L, 'GST', '29AAACX1234F1Z9', '29', 'Karnataka')
$sql$, :'tenant_id', :'client_id'));

-- GST whose positions 3-12 do NOT match the PAN: trigger blocks.
SELECT assert_raises(format($sql$
    INSERT INTO client_registrations (tenant_id, client_id, registration_type, identifier_value, state_code, state_name)
    VALUES (%L, %L, 'GST', '27ZZZZZ1234F1Z5', '27', 'Maharashtra')
$sql$, :'tenant_id', :'client_id'), 'positions 3-12 must equal client PAN');
