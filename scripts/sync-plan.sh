#!/usr/bin/env bash
# Push training_plan.html to COROS calendar, then Google Calendar when authenticated.
set -euo pipefail
cd "$(dirname "$0")/.."
bash scripts/sync-run.sh sync -y
if .venv/bin/coros-mcp calendar-sync; then
  echo ""
  echo "Google Calendar synced."
else
  echo ""
  echo "Google Calendar not synced — token expired or missing."
  echo "Run: coros-mcp calendar-auth --force"
  echo "Then: coros-mcp calendar-sync"
fi
