-- 0012_app_role.sql
-- Create a non-superuser application role that the API connects as.
--
-- This is a security-critical migration. Postgres superusers bypass RLS
-- regardless of FORCE ROW LEVEL SECURITY, so if the API connects as a
-- superuser, the tenant-isolation policies from 0009 are silently disabled
-- and queries return rows from every tenant. The API MUST connect as
-- ``noticedesk_app`` (or another non-superuser role); migrations and
-- schema tests run as the superuser ``noticedesk``.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'noticedesk_app') THEN
        -- LOGIN + a dev-only password so DATABASE_URL works out of the box.
        -- Production overrides the password from Secrets Manager.
        CREATE ROLE noticedesk_app
            WITH LOGIN PASSWORD 'noticedesk_app'
            NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
    END IF;
END $$;

GRANT USAGE ON SCHEMA public TO noticedesk_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO noticedesk_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO noticedesk_app;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO noticedesk_app;

-- Future tables/sequences created by later migrations get the same grants
-- automatically, so we don't have to remember to re-grant.
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO noticedesk_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE ON SEQUENCES TO noticedesk_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT EXECUTE ON FUNCTIONS TO noticedesk_app;
