#!/usr/bin/env bash
set -euo pipefail
PLIST="$HOME/Library/LaunchAgents/com.yordamkocatepe.mcp.yahoo.http.plist"
LABEL="com.yordamkocatepe.mcp.yahoo.http"
USER_ID="$(id -u)"
launchctl bootout gui/$USER_ID/$LABEL >/dev/null 2>&1 || true
launchctl bootstrap gui/$USER_ID "$PLIST"
launchctl enable gui/$USER_ID/$LABEL || true
launchctl kickstart -k gui/$USER_ID/$LABEL
sleep 1
launchctl print gui/$USER_ID/$LABEL | sed -n '1,200p' || true
if command -v lsof >/dev/null 2>&1; then
  echo "\nListening sockets (8000):"; lsof -nP -iTCP:8000 -sTCP:LISTEN || true
fi
