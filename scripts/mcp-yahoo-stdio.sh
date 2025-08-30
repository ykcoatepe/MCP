#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
export PYTHONPATH="$REPO_ROOT/yahoo/libs/py/mcp_yahoo/src"
export MCP_TRANSPORT=stdio

# Run within the Yahoo project so uv uses its pyproject/venv
cd "$REPO_ROOT/yahoo"
exec uv run python -m mcp_yahoo.server
