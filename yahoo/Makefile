.PHONY: setup run lint test
setup:
	uv venv --python 3.11 || true
	uv lock
	uv sync --frozen

run:
	PYTHONPATH=libs/py/mcp_yahoo/src uv run python -m mcp_yahoo.server

lint:
	uv run ruff check .

test:
	PYTHONPATH=libs/py/mcp_yahoo/src uv run pytest -q
