-- _helpers.sql
-- Shared assertion helpers used by the schema tests. All test scripts run
-- inside a transaction that is rolled back at the end, so seeded rows do
-- not persist between tests.

CREATE OR REPLACE FUNCTION assert_raises(stmt TEXT, expected_substr TEXT)
RETURNS VOID AS $$
DECLARE
    msg TEXT;
BEGIN
    BEGIN
        EXECUTE stmt;
        RAISE EXCEPTION 'assert_raises: statement did not raise: %', stmt;
    EXCEPTION WHEN others THEN
        msg := SQLERRM;
        IF expected_substr IS NOT NULL AND POSITION(expected_substr IN msg) = 0 THEN
            RAISE EXCEPTION 'assert_raises: expected %, got %', expected_substr, msg;
        END IF;
    END;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION assert_succeeds(stmt TEXT)
RETURNS VOID AS $$
BEGIN
    EXECUTE stmt;
END;
$$ LANGUAGE plpgsql;
