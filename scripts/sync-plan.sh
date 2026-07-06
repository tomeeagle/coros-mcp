#!/usr/bin/env bash
# Push training_plan.html to COROS calendar (upcoming sessions, no prompt).
set -euo pipefail
cd "$(dirname "$0")/.."
exec bash scripts/sync-run.sh sync -y
