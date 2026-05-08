DATABASE_URL ?= postgres://noticedesk:noticedesk@localhost:5432/noticedesk_dev
TEST_DATABASE_URL ?= postgres://noticedesk:noticedesk@localhost:5432/noticedesk_test

.PHONY: migrate test reset

migrate:
	@for f in migrations/*.sql; do \
		echo "applying $$f"; \
		psql "$(DATABASE_URL)" -v ON_ERROR_STOP=1 -f $$f >/dev/null; \
	done

test:
	DATABASE_URL="$(TEST_DATABASE_URL)" bash tests/run_all.sh

reset:
	psql "$(DATABASE_URL)" -v ON_ERROR_STOP=1 \
		-c "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;"
