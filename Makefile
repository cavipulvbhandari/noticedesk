.PHONY: db-test api-test web-test ci-local fmt lint typecheck

DATABASE_URL ?= postgres://noticedesk:noticedesk@localhost:5432/noticedesk_test

db-test:
	DATABASE_URL=$(DATABASE_URL) bash packages/db/tests/run_all.sh

api-test:
	cd apps/api && pytest

web-test:
	cd apps/web && npm run typecheck && npm run lint && npm run build

ci-local: db-test api-test web-test

fmt:
	cd apps/api && ruff format . || true
	cd infra && terraform fmt -recursive || true

lint:
	cd apps/api && ruff check .
	cd apps/web && npm run lint

typecheck:
	cd apps/api && mypy app
	cd apps/web && npm run typecheck
	cd packages/shared && npm run typecheck
