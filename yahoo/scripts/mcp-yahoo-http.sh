#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$(cd "$ROOT/libs/py/mcp_yahoo/src" && pwd)"
export MCP_TRANSPORT=http
exec uv run python -m mcp_yahoo.server

