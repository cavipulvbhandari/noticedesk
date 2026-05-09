-- 0010_users_clerk_link.sql
-- Link users to their Clerk identity. Brief specifies clerk_user_id as the
-- bridge between our user records and Clerk's hosted auth. Nullable so the
-- dev-bypass auth path (used in Sprint 1 local development) can still issue
-- sessions without a Clerk account.

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS clerk_user_id TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_clerk_user_id
    ON users (clerk_user_id)
    WHERE clerk_user_id IS NOT NULL;
