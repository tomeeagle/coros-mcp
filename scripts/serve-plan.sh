#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

PORT="${PORT:-8080}"
HOST="${HOST:-127.0.0.1}"
PLAN="${PLAN:-training_plan.html}"
AUTO_SYNC="${AUTO_SYNC:-1}"
# Browser always uses localhost (HOST=0.0.0.0 is bind-only)
OPEN_HOST="$HOST"
if [[ "$OPEN_HOST" == "0.0.0.0" ]]; then
  OPEN_HOST="127.0.0.1"
fi
URL="http://${OPEN_HOST}:${PORT}/${PLAN}"

open_url() {
  if command -v open >/dev/null 2>&1; then
    open "$URL"
  elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$URL"
  else
    echo "  Open in browser: ${URL}"
  fi
}

echo ""
echo "  Plan:  ${URL}"
if [[ "$AUTO_SYNC" == "1" ]]; then
  echo "  COROS: auto-sync on save (set AUTO_SYNC=0 to disable)"
fi
echo "  Ctrl+C to stop"
echo ""

if [[ "$AUTO_SYNC" == "1" ]]; then
  bash scripts/watch-plan-sync.sh &
  WATCH_PID=$!
  trap 'kill "$SRV_PID" "$WATCH_PID" 2>/dev/null' EXIT INT TERM
else
  trap 'kill "$SRV_PID" 2>/dev/null' EXIT INT TERM
fi

python3 -m http.server "$PORT" --bind "$HOST" &
SRV_PID=$!

sleep 0.4
open_url

wait "$SRV_PID"
