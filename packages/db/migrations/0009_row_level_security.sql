-- 0009_row_level_security.sql
-- Row-level security on every tenant-scoped table.
--
-- Each request must `SET app.current_tenant = '<tenant uuid>'` before issuing
-- queries. Without it the policy evaluates to FALSE and zero rows are visible.
-- The `tenants` table itself is intentionally not RLS-restricted: the API
-- layer chooses which tenant a session belongs to.

-- Helper: a SECURITY DEFINER function that returns NULL when app.current_tenant
-- is unset, instead of raising. This lets policies fail closed without
-- breaking unrelated DDL.
CREATE OR REPLACE FUNCTION current_tenant_id()
RETURNS UUID
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v TEXT;
BEGIN
    BEGIN
        v := current_setting('app.current_tenant', true);
    EXCEPTION WHEN others THEN
        RETURN NULL;
    END;
    IF v IS NULL OR v = '' THEN
        RETURN NULL;
    END IF;
    RETURN v::UUID;
END;
$$;

DO $$
DECLARE
    tbl TEXT;
    tenant_scoped TEXT[] := ARRAY[
        'users',
        'clients',
        'client_registrations',
        'matters',
        'notices',
        'documents',
        'drafts',
        'citations',
        'audit_logs',
        'cross_adjudication_flags',
        'reminders',
        'billing_entries'
    ];
BEGIN
    FOREACH tbl IN ARRAY tenant_scoped LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', tbl);
        EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', tbl);
        EXECUTE format('DROP POLICY IF EXISTS tenant_isolation ON %I', tbl);
        EXECUTE format(
            'CREATE POLICY tenant_isolation ON %I FOR ALL '
            'USING (tenant_id = current_tenant_id()) '
            'WITH CHECK (tenant_id = current_tenant_id())',
            tbl
        );
    END LOOP;
END $$;
