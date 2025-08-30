#!/usr/bin/env bash
set -euo pipefail
LABEL="com.yordamkocatepe.mcp.yahoo.http"
USER_ID="$(id -u)"
launchctl bootout gui/$USER_ID/$LABEL || true
