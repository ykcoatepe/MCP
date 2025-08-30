# Repository Guidelines

## Project Structure & Module Organization
- `libs/py/mcp_yahoo/src/mcp_yahoo/`: MCP server implementation
  - `server.py` (tools and transport), `cli.py` (entry), `schemas.py`, `metrics.py`, `config.py`
  - `providers/` — `yf.py` (yfinance), `rapid.py` (RapidAPI), `stub.py` (testing)
- `scripts/`: local runners and diagnostics (e.g., `mcp-yahoo-http.sh`, `diag-8000.sh`)
- `tests/`: pytest-based tests (add new tests here)
- `mcp_yahoo.toml`: runtime config (see Security & Config)
- `pyproject.toml`: deps (`uv`, `ruff`, `pytest`, `mypy`) and console entry (`mcp-yahoo`).

## Build, Test, and Development Commands
- `make setup` — create venv with `uv`, lock and install deps
- `make run-stdio` — start MCP server over stdio (preferred for Codex CLI)
- `make run-http` — start HTTP server at `http://127.0.0.1:8000/mcp`
- `make health` — quick health check (no network call)
- `make lint` — run Ruff
- `make test` — run pytest

Examples:
```
PYTHONPATH=libs/py/mcp_yahoo/src uv run python -m mcp_yahoo.server
```

## Coding Style & Naming Conventions
- Python 3.11+, PEP 8; 2‑space? 4‑space indentation (use 4)
- Ruff enforced (line length 100). Type‑check with `mypy --strict`.
- Names: modules/functions `lower_snake_case`, classes `PascalCase`, constants `UPPER_SNAKE_CASE`.

## Testing Guidelines
- Framework: `pytest`. Place files as `tests/test_*.py` matching module names.
- Prefer fast, deterministic tests. For network isolation use the stub or recorded data.
- Run: `make test` (CI should pass lint + tests).

## Commit & Pull Request Guidelines
- Use Conventional Commits (e.g., `feat: add options chain tool`, `fix(yf): handle null price`).
- Keep PRs focused; include:
  - What/why, screenshots or logs for behavior, and reproduction steps.
  - Update docs when changing tools, config, or scripts.

## Security & Configuration Tips
- Never commit secrets. Configure via env or `mcp_yahoo.toml`:
  - `PROVIDER`=`yfinance|rapidapi`; `RAPIDAPI_KEY` via env; optional `RAPIDAPI_HOST`, `RAPIDAPI_REGION`.
- For local runs set transport via env: `MCP_TRANSPORT=stdio|http`.
- Use `configz()` to verify effective config (keys are redacted).

## Agent-Specific Notes
- Codex CLI: point an MCP entry to the `mcp-yahoo` console script (stdio) or a wrapper in `scripts/`.
- HTTP mode is for hosts that can reach `http://127.0.0.1:8000/mcp`; prefer stdio for local development.

