#!/usr/bin/env bash
# Apply all migrations and run schema tests against $DATABASE_URL.
#
# Each test file in tests/*.sql is run with helpers prepended and wrapped in
# BEGIN/ROLLBACK so it doesn't leak state to subsequent tests.
#
# Usage:
#   DATABASE_URL=postgres://noticedesk:noticedesk@localhost:5432/noticedesk_test \
#     bash packages/db/tests/run_all.sh
set -euo pipefail

: "${DATABASE_URL:?DATABASE_URL must be set}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HELPERS="$ROOT/tests/_helpers.sql"

echo "==> Resetting schema"
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 \
    -c "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;" >/dev/null

echo "==> Applying migrations"
for f in "$ROOT"/migrations/*.sql; do
    echo "  - $(basename "$f")"
    psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$f" >/dev/null
done

echo "==> Loading test helpers"
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$HELPERS" >/dev/null

echo "==> Running tests"
for f in "$ROOT"/tests/*.sql; do
    name="$(basename "$f")"
    if [ "$name" = "_helpers.sql" ]; then continue; fi
    echo "  - $name"
    # Each test runs in its own transaction and is rolled back so RLS state /
    # seeded rows do not carry over.
    {
        echo 'BEGIN;'
        cat "$f"
        echo 'ROLLBACK;'
    } | psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -q -f - >/dev/null
done

echo "==> All schema tests passed"
