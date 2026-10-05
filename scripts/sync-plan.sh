#!/usr/bin/env bash
# Push training_plan.html to COROS calendar.
#
# Google Calendar is no longer synced from here — the HTML-driven full
# calendar-sync would silently recreate stale/duplicate events on top of
# any day someone edited directly on COROS. Google Calendar is now mirrored
# by hand for whatever's actually changed, not reconciled from the plan file.
set -euo pipefail
cd "$(dirname "$0")/.."
bash scripts/sync-run.sh sync -y
