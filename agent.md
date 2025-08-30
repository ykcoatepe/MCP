# MCP Agents – Yahoo (Python) and SQLite (Node)

This repo contains two Model Context Protocol (MCP) servers:

- Yahoo MCP (Python, uv): real data provider (yfinance by default), optional RapidAPI, stdio/http/sse transports, TTL caches, retries, health, and JSON logs.
- SQLite MCP (Node.js ESM): stdio server exposing simple SQLite tools.

Use this doc to set up, run, and integrate them with Codex CLI or a Desktop Connector.

## Prerequisites

- Python 3.11+
- uv (Python package manager): https://docs.astral.sh/uv/
- Node.js 20 (see `sqlite/.nvmrc`); npm
- Git installed and repo cloned

## Branch

- Current working branch: `dev_yordam` (pushed to origin)

## Yahoo MCP (Python)

Location:

- Server: `yahoo/libs/py/mcp_yahoo/src/mcp_yahoo/server.py`
- Providers: `yahoo/libs/py/mcp_yahoo/src/mcp_yahoo/providers/yf.py` (default), `providers/rapid.py` (RapidAPI)
- Config loader: `yahoo/libs/py/mcp_yahoo/src/mcp_yahoo/config.py`
- Caches: `yahoo/libs/py/mcp_yahoo/src/mcp_yahoo/cache.py`
- Makefile: `yahoo/Makefile`

Install deps (isolated):

```bash
make -C yahoo setup
```

Run locally (stdio):

```bash
# via Makefile helper
make -C yahoo run-stdio

# or direct
PYTHONPATH=yahoo/libs/py/mcp_yahoo/src \
  MCP_TRANSPORT=stdio \
  uv run python -m mcp_yahoo.server
```

Run tests:

```bash
make -C yahoo test
```

### Codex integration (stdio)

- Launcher: `scripts/mcp-yahoo-stdio.sh`
- Codex config (usually `~/.codex/config.toml`):

```toml
[mcp_servers.yahoo]
command = "/ABSOLUTE/PATH/TO/REPO/scripts/mcp-yahoo-stdio.sh"

[projects]
"/ABSOLUTE/PATH/TO/REPO" = { trust_level = "trusted" }
```

Validate in Codex: list MCP servers/tools; call `search("AAPL")`, `fetch("AAPL")`, `get_quote(symbol="MSFT")`.

### Desktop Connector (HTTP)

- HTTP runner: `yahoo/scripts/mcp-yahoo-http.sh` (binds `http://127.0.0.1:8000/mcp`)
- Port diagnostics: `yahoo/scripts/diag-8000.sh`
- Makefile helpers: `make -C yahoo run-http`, `make -C yahoo health`
- Guide: `yahoo/README_CONNECTOR.md`

If port 8000 is busy, use the diag script to find/stop the blocker.

### Tools

- `search(query)`, `fetch(id)`
- `get_quote(symbol)`
- `get_history(symbol, start?, end?, interval="1d", adjust=true)`
- `get_options_chain(symbol, expiry?)`
- `healthz(deep=false|true)`
- `configz()` (effective provider/config; RapidAPI key redacted)

### Configuration

- Sample TOML: `yahoo/mcp_yahoo.toml`
- Env overrides (common):
  - `PROVIDER=yfinance|rapidapi`
  - `RAPIDAPI_KEY`, `RAPIDAPI_HOST`, `RAPIDAPI_REGION` (default `US`)
  - Transports: `MCP_TRANSPORT=stdio|http|sse`
- Introspection: call `configz()` to see the effective config.

### Caching, Retries, Logs

- TTL caches for search/quote/history/options (durations via env in `mcp_yahoo/cache.py`).
- Exponential backoff + jitter for network calls.
- JSON logs for tool_ok/tool_err with durations to stdout (intended for diagnostics).

## SQLite MCP (Node)

Location:

- Code/entry: `sqlite/index.js` (ESM)
- Docs: `sqlite/README.md`, `sqlite/AGENTS.md`

Install and run:

```bash
cd sqlite
npm install
node index.js   # stdio server (stays quiet on stdout)

# Smoke test
npm test
```

Environment:

- `SQLITE_DB` or `MCP_SQLITE_DB` for DB path (default `./portfolio.db`)
- Optional bootstrap SQL via `SQLITE_BOOTSTRAP` or `MCP_SQLITE_BOOTSTRAP`

## Development Tips

- Prefer stdio transport for local MCP development.
- Yahoo server supports `stdio`, `sse` (with `MCP_TRANSPORT=sse`), and HTTP.
- Use Conventional Commits for PRs.

## Common Commands

```bash
# Yahoo (setup, run stdio/http, test, health)
make -C yahoo setup
make -C yahoo run-stdio
make -C yahoo run-http
make -C yahoo health
make -C yahoo test

# SQLite (install, run, test)
(cd sqlite && npm install && node index.js)
(cd sqlite && npm test)
```

## Troubleshooting

- Node native bindings (SQLite): use Node 20; if build errors, reinstall deps
  - In `sqlite/`: `rm -rf node_modules package-lock.json && npm install`
- uv not found: install from Astral docs and re-run `make -C yahoo setup`.
- Codex can’t find Yahoo server: verify absolute path in config and executable bit on launcher.
- If uv cache errors appear, set a project-local cache: `UV_CACHE_DIR="$(pwd)/yahoo/.uv-cache" make -C yahoo setup`.

## Current Feature Summary

- Real data via yfinance (default provider).
- Optional RapidAPI provider with region support (search/quote implemented).
- Tools: search, fetch, get_quote, get_history, get_options_chain, healthz, configz.
- Caching (TTL), retries/backoff, JSON logs.
- Stdio launcher for Codex; HTTP runner and diagnostics for Desktop.

## Sanity & Tests

- Sanity: `scripts/sanity_task12.sh` (files, setup/tests, HTTP bind check, stdio launcher, stub logic).
- Unit/Network tests under `yahoo/tests/` (enable network with `RUN_NETWORK_TESTS=1`, RapidAPI with `RUN_RAPIDAPI_TESTS=1`).
