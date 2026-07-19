-- 0017_clients_email_phone.sql
-- Client contact details. Email is the channel triage uses to send the
-- document checklist to the client; phone is optional, for future WhatsApp /
-- SMS reminders. Both nullable: partners can run triage on a client without
-- contact info on file (the checklist email is best-effort and silently
-- skipped when email is null).

ALTER TABLE clients
    ADD COLUMN IF NOT EXISTS email TEXT,
    ADD COLUMN IF NOT EXISTS phone TEXT;

-- Sanity-check format constraints. Loose by design — production-grade
-- validation happens at the API boundary (email-validator package).
ALTER TABLE clients DROP CONSTRAINT IF EXISTS clients_email_format;
ALTER TABLE clients
    ADD CONSTRAINT clients_email_format
    CHECK (email IS NULL OR email ~* '^[^@\s]+@[^@\s]+\.[^@\s]+$');

CREATE INDEX IF NOT EXISTS idx_clients_email
    ON clients (tenant_id, LOWER(email))
    WHERE email IS NOT NULL AND deleted_at IS NULL;
