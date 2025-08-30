#!/usr/bin/env bash
set -euo pipefail
ROOT="/Users/yordamkocatepe/mcp/yahoo"
export PYTHONPATH="$ROOT/libs/py/mcp_yahoo/src"
export MCP_TRANSPORT=stdio
cd "$ROOT"
exec uv run python -m mcp_yahoo.server
