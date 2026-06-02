#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

PY=".venv/bin/python"
if [[ ! -x "$PY" ]]; then
  echo "No .venv found. Run: npm run sync:setup" >&2
  exit 1
fi

exec "$PY" coros_sync.py "$@"
