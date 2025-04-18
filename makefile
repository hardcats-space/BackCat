.PHONY: dev
dev:
	uv run litestar --app backcat.cmd.server:app run --reload-dir backcat --port 8080 --host 127.0.0.1 --debug

.PHONY: migration
migration:
	 uv run piccolo migrations new backcat_database

.PHONY: migration-up
migration-up:
	uv run piccolo migrations forward all

.PHONY: migration-down
migration-down:
	uv run piccolo migrations backward all

.PHONY: typescript
typescript:
	uv run litestar --app backcat.cmd.server:app schema typescript --output dist/hardcats.ts

.PHONY: openapi
openapi:
	uv run litestar --app backcat.cmd.server:app schema openapi --output dist/openapi.json