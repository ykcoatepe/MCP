# MCP Agents – Yahoo (Python) and SQLite (Node)

This repo contains two Model Context Protocol (MCP) servers:

- Yahoo MCP (Python, uv): stub search/fetch tools, stdio/http/sse transports
- SQLite MCP (Node.js ESM): stdio server exposing simple SQLite tools

Use this doc to set up, run, and integrate them with Codex CLI.

## Prerequisites

- Python 3.11+
- uv (Python package manager): https://docs.astral.sh/uv/
- Node.js 20 (see `sqlite/.nvmrc`); npm
- Git installed and repo cloned

## Branch

- Current working branch: `dev_yordam` (pushed to origin)

## Yahoo MCP (Python)

Location:

- Code: `yahoo/libs/py/mcp_yahoo/src/mcp_yahoo/`
- Entry: `yahoo/libs/py/mcp_yahoo/src/mcp_yahoo/server.py`
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

Launcher script:

- `scripts/mcp-yahoo-stdio.sh` (added)

Codex config (usually `~/.codex/config.toml`):

```toml
[mcp_servers.yahoo]
command = "/ABSOLUTE/PATH/TO/REPO/scripts/mcp-yahoo-stdio.sh"

[projects]
"/ABSOLUTE/PATH/TO/REPO" = { trust_level = "trusted" }
```

Validation inside Codex:

- Start a session in this project
- Ensure server `yahoo` appears with tools `search`, `fetch`
- Try `search("AAPL")` and `fetch("AAPL")` → returns stub data

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

- Prefer stdio transport for local MCP development
- Yahoo server supports `stdio`, `sse` (with `MCP_TRANSPORT=sse`), and streamable HTTP
- Keep stdout clean; log to stderr only when needed
- Use Conventional Commits for PRs

## Common Commands

```bash
# Yahoo (setup, run stdio, test)
make -C yahoo setup
make -C yahoo run-stdio
make -C yahoo test

# SQLite (install, run, test)
(cd sqlite && npm install && node index.js)
(cd sqlite && npm test)
```

## Troubleshooting

- Node native bindings (SQLite): use Node 20; if build errors, reinstall deps
  - In `sqlite/`: `rm -rf node_modules package-lock.json && npm install`
- uv not found: install from Astral docs and re-run `make -C yahoo setup`
- Codex can’t find Yahoo server: verify absolute path in config and executable bit on launcher

## Roadmap (from plan)

1) Scaffold + stub MCP (search/fetch)
2) Codex stdio wiring (done here)
3) Swap stub → yfinance provider; add `get_quote`
4) `get_history` + tests
5) `get_options_chain` + tests
6) Caching (TTL), retries/backoff, `/healthz`, JSON logs
7) Config + optional licensed provider switch

