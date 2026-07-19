-- 0008_reminders_billing.sql

CREATE TABLE IF NOT EXISTS reminders (
    reminder_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id        UUID NOT NULL REFERENCES tenants (tenant_id) ON DELETE RESTRICT,
    matter_id        UUID NOT NULL REFERENCES matters (matter_id) ON DELETE RESTRICT,
    target_user_id   UUID REFERENCES users (user_id),
    scheduled_at     TIMESTAMPTZ,
    channel          TEXT CHECK (channel IN ('whatsapp', 'sms', 'email', 'call')),
    state            TEXT CHECK (state IN ('scheduled', 'sent', 'delivered', 'acted', 'cancelled')),
    retry_count      INT NOT NULL DEFAULT 0,
    escalation_level INT NOT NULL DEFAULT 1,
    last_attempt     TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_reminders_matter        ON reminders (matter_id);
CREATE INDEX IF NOT EXISTS idx_reminders_scheduled     ON reminders (tenant_id, scheduled_at) WHERE state = 'scheduled';

CREATE TABLE IF NOT EXISTS billing_entries (
    entry_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants (tenant_id) ON DELETE RESTRICT,
    matter_id           UUID NOT NULL REFERENCES matters (matter_id) ON DELETE RESTRICT,
    time_spent_minutes  INT,
    partner_minutes     INT,
    staff_minutes       INT,
    complexity_score    INT,
    suggested_fee       NUMERIC,
    actual_billed       NUMERIC,
    write_off_amount    NUMERIC,
    status              TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_billing_matter ON billing_entries (matter_id);
