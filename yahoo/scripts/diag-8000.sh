#!/usr/bin/env bash
set -euo pipefail
echo "Checking listeners on port 8000..."
if command -v lsof >/dev/null 2>&1; then
  lsof -nP -iTCP:8000 -sTCP:LISTEN || true
else
  echo "lsof not found; install via: brew install lsof"
fi
echo "Tip: To kill a process: kill -9 <PID>"

