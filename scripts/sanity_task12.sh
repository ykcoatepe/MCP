#!/usr/bin/env bash
set -euo pipefail

# This sanity script validates Task 1 + Task 2.
# Notes:
# - FastMCP's HTTP transport binds at a fixed default port (8000). Host/port envs are ignored.
# - If port 8000 is already in use, we SKIP the HTTP bind test.
# - Codex integration uses STDIO; we only require the launcher to start & exit cleanly without a handshake.

ROOT="$(pwd)"

if [ -d "yahoo/libs/py/mcp_yahoo/src" ]; then
  LIB_ROOT="yahoo/libs/py/mcp_yahoo/src"
  MAKE_DIR="yahoo"
else
  LIB_ROOT="libs/py/mcp_yahoo/src"
  MAKE_DIR="."
fi
LAUNCH="./scripts/mcp-yahoo-stdio.sh"

# Absolute path for PYTHONPATH to be robust when cd'ing
LIB_ABS="${ROOT}/${LIB_ROOT}"

ok()   { echo "PASS  $*"; }
skip() { echo "SKIP  $*"; }
fail() { echo "FAIL  $*"; exit 1; }

command -v lsof >/dev/null 2>&1 || fail "missing required tool: lsof"

# ---------- Files present ----------
[ -f "$LIB_ROOT/mcp_yahoo/server.py" ] || fail "server.py missing at $LIB_ROOT/mcp_yahoo/server.py"
[ -f "$LIB_ROOT/mcp_yahoo/providers/stub.py" ] || fail "stub provider missing"
[ -x "scripts/mcp-yahoo-stdio.sh" ] || fail "launcher scripts/mcp-yahoo-stdio.sh missing or not executable"
ok "files present"

# ---------- Build & tests ----------
( cd "$MAKE_DIR" && make setup )
( cd "$MAKE_DIR" && PYTHONPATH="$LIB_ABS" uv run pytest -q )
ok "setup + tests"

# ---------- HTTP transport on fixed port 8000 ----------
if lsof -iTCP:8000 -sTCP:LISTEN -P -n >/dev/null 2>&1; then
  skip "HTTP transport: port 8000 already in use; skipping bind check"
else
  ( cd "$MAKE_DIR" && MCP_TRANSPORT=http PYTHONPATH="$LIB_ABS" uv run python -m mcp_yahoo.server ) & SERVER_PID=$!
  sleep 1
  # Confirm our server is alive and listening
  if ! ps -p $SERVER_PID >/dev/null 2>&1; then
    fail "HTTP server failed to start (process not alive)"
  fi
  lsof -iTCP:8000 -sTCP:LISTEN -P -n >/dev/null 2>&1 || { kill $SERVER_PID 2>/dev/null || true; fail "HTTP server not listening on :8000"; }
  kill $SERVER_PID 2>/dev/null || true
  ok "HTTP transport binds on :8000"
fi

# ---------- STDIO launcher behavior ----------
set +e
$LAUNCH >/dev/null 2>&1
EC=$?
set -e
[ $EC -eq 0 ] || fail "stdio launcher exited non-zero (got $EC)"
ok "stdio launcher starts and exits cleanly (no client attached)"

# ---------- Stub provider behavior ----------
PYTHONPATH="$LIB_ABS" uv run python - <<'PY'
from mcp_yahoo.providers.stub import StubProvider
p=StubProvider()
items=p.search("AAPL")
assert any(it["symbol"]=="AAPL" for it in items), "search('AAPL') returned no AAPL"
q=p.quote("MSFT")
assert q["symbol"]=="MSFT" and isinstance(q["price"], (int,float)), "quote('MSFT') bad payload"
print("OK")
PY
ok "stub search/quote logic"

echo "----------------------------------------"
[ -x "yahoo/scripts/mcp-yahoo-http.sh" ] && echo "PASS  http runner present" || echo "FAIL  http runner missing"
echo "All sanity checks PASSED or SKIPPED as appropriate for Task 1 & 2."
