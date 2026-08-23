-- 0010_tenant_slug.sql
-- Per-tenant slug used for inbound email routing
-- (notices+{slug}@noticedesk.in) and other URL-friendly references.
--
-- Globally unique (an email address can only resolve to one tenant). Auto-
-- generated from legal_name on insert if the caller doesn't supply one;
-- a trigger ensures uniqueness by appending an incrementing counter.

ALTER TABLE tenants
    ADD COLUMN IF NOT EXISTS slug TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_tenants_slug ON tenants (slug)
    WHERE slug IS NOT NULL;

ALTER TABLE tenants
    DROP CONSTRAINT IF EXISTS tenant_slug_format;
ALTER TABLE tenants
    ADD CONSTRAINT tenant_slug_format
    CHECK (slug IS NULL OR slug ~ '^[a-z0-9]([a-z0-9-]{0,46}[a-z0-9])?$');

CREATE OR REPLACE FUNCTION slugify(input TEXT)
RETURNS TEXT AS $$
DECLARE
    s TEXT;
BEGIN
    IF input IS NULL THEN
        RETURN NULL;
    END IF;
    s := lower(input);
    s := regexp_replace(s, '[^a-z0-9]+', '-', 'g');
    s := regexp_replace(s, '^-+|-+$', '', 'g');
    s := substring(s FROM 1 FOR 48);
    s := regexp_replace(s, '^-+|-+$', '', 'g');
    IF s = '' THEN
        RETURN NULL;
    END IF;
    RETURN s;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Trigger: auto-assign a unique slug when one isn't provided.
CREATE OR REPLACE FUNCTION ensure_tenant_slug()
RETURNS TRIGGER AS $$
DECLARE
    base TEXT;
    candidate TEXT;
    suffix INT := 1;
BEGIN
    IF NEW.slug IS NOT NULL THEN
        RETURN NEW;
    END IF;
    base := slugify(NEW.legal_name);
    IF base IS NULL THEN
        base := 'tenant';
    END IF;
    candidate := base;
    WHILE EXISTS (SELECT 1 FROM tenants WHERE slug = candidate AND tenant_id <> NEW.tenant_id) LOOP
        suffix := suffix + 1;
        candidate := substring(base FROM 1 FOR 44) || '-' || suffix::TEXT;
    END LOOP;
    NEW.slug := candidate;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_ensure_tenant_slug ON tenants;
CREATE TRIGGER trg_ensure_tenant_slug
    BEFORE INSERT OR UPDATE OF legal_name, slug ON tenants
    FOR EACH ROW EXECUTE FUNCTION ensure_tenant_slug();

-- Backfill: re-touch legal_name on existing rows that don't yet have a slug
-- so the trigger above runs and assigns one.
UPDATE tenants SET legal_name = legal_name WHERE slug IS NULL;
