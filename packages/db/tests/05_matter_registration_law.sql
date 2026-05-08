-- 05_matter_registration_law.sql — trigger enforces matters.law matches the registration's type.

INSERT INTO tenants (legal_name) VALUES ('Test Firm') RETURNING tenant_id \gset

INSERT INTO clients (tenant_id, pan, legal_name)
VALUES (:'tenant_id', 'AAACX1234F', 'Acme Pvt Ltd')
RETURNING client_id \gset

INSERT INTO client_registrations (tenant_id, client_id, registration_type, identifier_value)
VALUES (:'tenant_id', :'client_id', 'IT', 'AAACX1234F')
RETURNING registration_id AS it_reg_id \gset

INSERT INTO client_registrations (tenant_id, client_id, registration_type, identifier_value, state_code, state_name)
VALUES (:'tenant_id', :'client_id', 'GST', '27AAACX1234F1Z5', '27', 'Maharashtra')
RETURNING registration_id AS gst_reg_id \gset

-- Matter on IT registration with law='IT': succeeds.
SELECT assert_succeeds(format($sql$
    INSERT INTO matters (tenant_id, client_id, registration_id, law, financial_year, assessment_year)
    VALUES (%L, %L, %L, 'IT', '2022-23', '2023-24')
$sql$, :'tenant_id', :'client_id', :'it_reg_id'));

-- Matter on GST registration with law='GST': succeeds.
SELECT assert_succeeds(format($sql$
    INSERT INTO matters (tenant_id, client_id, registration_id, law, financial_year)
    VALUES (%L, %L, %L, 'GST', '2022-23')
$sql$, :'tenant_id', :'client_id', :'gst_reg_id'));

-- Matter on GST registration with law='IT': trigger blocks.
SELECT assert_raises(format($sql$
    INSERT INTO matters (tenant_id, client_id, registration_id, law, financial_year)
    VALUES (%L, %L, %L, 'IT', '2022-23')
$sql$, :'tenant_id', :'client_id', :'gst_reg_id'), 'must match the registration_type');

-- Matter on IT registration with law='GST': trigger blocks.
SELECT assert_raises(format($sql$
    INSERT INTO matters (tenant_id, client_id, registration_id, law, financial_year)
    VALUES (%L, %L, %L, 'GST', '2022-23')
$sql$, :'tenant_id', :'client_id', :'it_reg_id'), 'must match the registration_type');
