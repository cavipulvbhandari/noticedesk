-- 07_tenant_isolation.sql — RLS isolates rows between tenants.
--
-- Postgres superusers bypass RLS unless FORCE ROW LEVEL SECURITY is set on
-- the table (which migration 0009 does). Even with FORCE, superusers still
-- bypass — that's a Postgres invariant. We therefore `SET LOCAL ROLE` to the
-- non-superuser ``noticedesk_app`` (created by migration 0012) to mirror
-- what application connections see in production.

-- Seed two tenants, each with a client, as the privileged role (bypassing RLS for setup).
INSERT INTO tenants (legal_name) VALUES ('Firm A') RETURNING tenant_id AS tenant_a \gset
INSERT INTO tenants (legal_name) VALUES ('Firm B') RETURNING tenant_id AS tenant_b \gset

-- Insert seed clients with the right tenant context so WITH CHECK passes.
SET LOCAL ROLE noticedesk_app;
SELECT set_config('app.current_tenant', :'tenant_a', true);
INSERT INTO clients (tenant_id, pan, legal_name) VALUES (:'tenant_a', 'AAACX1234F', 'Client A');

SELECT set_config('app.current_tenant', :'tenant_b', true);
INSERT INTO clients (tenant_id, pan, legal_name) VALUES (:'tenant_b', 'BBBCX1234F', 'Client B');

-- As tenant A, only Firm A's client is visible.
SELECT set_config('app.current_tenant', :'tenant_a', true);
DO $$
DECLARE
    cnt INT;
    name TEXT;
BEGIN
    SELECT COUNT(*) INTO cnt FROM clients;
    IF cnt <> 1 THEN
        RAISE EXCEPTION 'expected 1 client visible to tenant A, got %', cnt;
    END IF;
    SELECT legal_name INTO name FROM clients;
    IF name <> 'Client A' THEN
        RAISE EXCEPTION 'expected Client A, got %', name;
    END IF;
END $$;

-- As tenant B, only Firm B's client is visible.
SELECT set_config('app.current_tenant', :'tenant_b', true);
DO $$
DECLARE
    cnt INT;
    name TEXT;
BEGIN
    SELECT COUNT(*) INTO cnt FROM clients;
    IF cnt <> 1 THEN
        RAISE EXCEPTION 'expected 1 client visible to tenant B, got %', cnt;
    END IF;
    SELECT legal_name INTO name FROM clients;
    IF name <> 'Client B' THEN
        RAISE EXCEPTION 'expected Client B, got %', name;
    END IF;
END $$;

-- With no tenant set, zero rows are visible.
SELECT set_config('app.current_tenant', '', true);
DO $$
DECLARE
    cnt INT;
BEGIN
    SELECT COUNT(*) INTO cnt FROM clients;
    IF cnt <> 0 THEN
        RAISE EXCEPTION 'expected 0 clients visible with no tenant set, got %', cnt;
    END IF;
END $$;

-- WITH CHECK: tenant A cannot insert rows scoped to tenant B.
SELECT set_config('app.current_tenant', :'tenant_a', true);
SELECT assert_raises(format($sql$
    INSERT INTO clients (tenant_id, pan, legal_name) VALUES (%L, 'CCCCX1234F', 'Wrong')
$sql$, :'tenant_b'), 'row-level security');

RESET ROLE;
