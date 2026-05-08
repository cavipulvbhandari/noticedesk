-- 01_pan_format.sql — clients.pan CHECK constraint.

INSERT INTO tenants (legal_name) VALUES ('Acme & Co') RETURNING tenant_id \gset

-- Valid PAN: succeeds.
SELECT assert_succeeds(format(
    $sql$ INSERT INTO clients (tenant_id, pan, legal_name) VALUES (%L, 'AAACX1234F', 'Acme Pvt Ltd') $sql$,
    :'tenant_id'
));

-- Invalid: missing trailing letter.
SELECT assert_raises(format(
    $sql$ INSERT INTO clients (tenant_id, pan, legal_name) VALUES (%L, 'ABCDE1234X9', 'Bad PAN 1') $sql$,
    :'tenant_id'
), 'pan_format');

-- Invalid: lowercase.
SELECT assert_raises(format(
    $sql$ INSERT INTO clients (tenant_id, pan, legal_name) VALUES (%L, 'aaacx1234f', 'Bad PAN 2') $sql$,
    :'tenant_id'
), 'pan_format');

-- Invalid: digits in alpha positions.
SELECT assert_raises(format(
    $sql$ INSERT INTO clients (tenant_id, pan, legal_name) VALUES (%L, '12345AAAAA', 'Bad PAN 3') $sql$,
    :'tenant_id'
), 'pan_format');

-- Invalid: too short.
SELECT assert_raises(format(
    $sql$ INSERT INTO clients (tenant_id, pan, legal_name) VALUES (%L, 'AAACX1234', 'Bad PAN 4') $sql$,
    :'tenant_id'
), 'pan_format');
