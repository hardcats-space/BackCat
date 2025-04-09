.PHONY: dev
dev:
	uv run litestar --app backcat.cmd.server:app run --reload-dir backcat --port 8080 --host 127.0.0.1 --debug