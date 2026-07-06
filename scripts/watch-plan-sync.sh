#!/usr/bin/env bash
# Watch training_plan.html and run COROS sync whenever it changes.
set -euo pipefail
cd "$(dirname "$0")/.."

PLAN="${PLAN:-training_plan.html}"
PY=".venv/bin/python"
INTERVAL="${PLAN_SYNC_INTERVAL:-2}"

if [[ ! -f "$PLAN" ]]; then
  echo "Plan not found: $PLAN" >&2
  exit 1
fi
if [[ ! -x "$PY" ]]; then
  echo "No .venv — run: npm run sync:setup" >&2
  exit 1
fi

plan_hash() {
  if command -v md5 >/dev/null 2>&1; then
    md5 -q "$PLAN"
  else
    md5sum "$PLAN" | awk '{print $1}'
  fi
}

echo "Watching $PLAN — COROS sync on save (every ${INTERVAL}s check)"
echo "  Initial sync..."
bash scripts/sync-plan.sh || echo "  ⚠️  Initial sync failed" >&2

last="$(plan_hash)"
while true; do
  sleep "$INTERVAL"
  current="$(plan_hash)"
  if [[ "$current" != "$last" ]]; then
    last="$current"
    echo ""
    echo "  $(date '+%H:%M:%S') — plan saved, syncing COROS..."
    bash scripts/sync-plan.sh || echo "  ⚠️  Sync failed" >&2
  fi
done
