-- 08_tenant_slug.sql — auto-generated, globally-unique tenant slugs.

DO $$
DECLARE
    s1 TEXT;
    s2 TEXT;
    s3 TEXT;
BEGIN
    INSERT INTO tenants (legal_name) VALUES ('Mehta & Associates') RETURNING slug INTO s1;
    IF s1 <> 'mehta-associates' THEN
        RAISE EXCEPTION 'expected slug mehta-associates, got %', s1;
    END IF;

    -- Second tenant with the same legal name gets a -2 suffix.
    INSERT INTO tenants (legal_name) VALUES ('Mehta & Associates') RETURNING slug INTO s2;
    IF s2 <> 'mehta-associates-2' THEN
        RAISE EXCEPTION 'expected slug mehta-associates-2, got %', s2;
    END IF;

    -- Punctuation-only legal_name still produces a usable slug.
    INSERT INTO tenants (legal_name) VALUES ('!!!') RETURNING slug INTO s3;
    IF s3 IS NULL OR s3 = '' THEN
        RAISE EXCEPTION 'expected non-empty fallback slug, got %', s3;
    END IF;
END $$;

-- Format check: rejects uppercase / underscores / leading or trailing hyphen.
SELECT assert_raises($$
    INSERT INTO tenants (legal_name, slug) VALUES ('Bad', 'Has_Underscore')
$$, 'tenant_slug_format');

SELECT assert_raises($$
    INSERT INTO tenants (legal_name, slug) VALUES ('Bad', '-leading-hyphen')
$$, 'tenant_slug_format');

SELECT assert_raises($$
    INSERT INTO tenants (legal_name, slug) VALUES ('Bad', 'trailing-hyphen-')
$$, 'tenant_slug_format');

-- Globally unique: explicit duplicate slug is rejected.
INSERT INTO tenants (legal_name, slug) VALUES ('Foo', 'foo-firm');
SELECT assert_raises($$
    INSERT INTO tenants (legal_name, slug) VALUES ('Foo Two', 'foo-firm')
$$, 'idx_tenants_slug');
