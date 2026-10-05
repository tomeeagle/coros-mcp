# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`coros-mcp` is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that exposes Coros fitness data (sleep, HRV, training metrics, activities, workouts) to AI assistants. It uses the **unofficial** Coros API — no official API key required.

## Setup & Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Running the Server

```bash
# Run via CLI entry point (recommended):
coros-mcp serve

# Or register with Claude Code:
claude mcp add coros -- /path/to/coros-mcp/.venv/bin/coros-mcp serve
```

## CLI Commands

```bash
coros-mcp auth           # Authenticate (web + mobile tokens)
coros-mcp auth-web       # Web API only (no sleep data)
coros-mcp auth-mobile    # Mobile API only (sleep data)
coros-mcp auth-status    # Check token status
coros-mcp auth-clear     # Remove stored tokens
coros-mcp sync [--from YYYYMMDD] [--to YYYYMMDD]  # Backfill data to local cache
coros-mcp cache-status   # Show local cache coverage
```

## Architecture

The project wraps two separate Coros APIs behind a unified MCP interface:

### Dual API Design
- **Training Hub web API** (`teameuapi.coros.com` / `teamapi.coros.com`): HRV, daily metrics, activities, workouts. Auth via MD5-hashed password → `accessToken` header. Token TTL: 24 hours.
- **Mobile API** (`apieu.coros.com` / `apius.coros.com`): Sleep stage data (deep/light/REM/awake). Auth via AES-128-CBC encrypted credentials (key reverse-engineered from Coros APK). Token TTL: ~1 hour, **auto-refreshes** by replaying the stored encrypted login payload.

### Token Storage (`auth/`)
Priority chain for retrieval: `COROS_ACCESS_TOKEN` env var → system keyring → encrypted local file. On write, both keyring and encrypted file are updated (belt-and-suspenders). The entire `StoredAuth` object (web token + mobile token + mobile login payload for replay) is serialized as JSON and stored as a single credential.

### Key Files
- **`server.py`**: FastMCP tool definitions. Each `@mcp.tool()` function validates auth, delegates to `coros_api`, and returns a dict. This is the only file that imports from `fastmcp`.
- **`coros_api.py`**: All HTTP logic. Contains two sets of endpoints (Training Hub + mobile), the AES encryption for mobile auth, auto-refresh logic, and response parsers. The `fetch_daily_records()` function merges two endpoints: `/analyse/dayDetail/query` (long range, no VO2max) + `/analyse/query` (last 28 days, has VO2max/fitness fields).
- **`models.py`**: Pydantic v2 models: `StoredAuth`, `DailyRecord`, `SleepRecord`/`SleepPhases`, `HRVRecord`, `ActivitySummary`.
- **`cli.py`**: CLI entry point registered as `coros-mcp` script. Delegates to `coros_api.login()` / `login_mobile()` and `cache.sync.sync_all()`.
- **`cache/`**: SQLite-backed local data store. `store.py` — raw read/write; `sync.py` — smart fetch logic (resolve gaps, backfill, chunk), `_resolve_fetch_range()` decides what to hit the API for; `utils.py` — timezone helpers.
- **`auth/`**: Token storage abstraction. Priority chain: env var → encrypted file → keyring. `encrypted_store.py` uses AES-256-GCM with a machine-bound key; `keyring_store.py` wraps the system keyring.

### API Response Pattern
All Coros API responses return `result: "0000"` on success. Any other value indicates an error — check `message` field. Large time-series fields (`graphList`, `frequencyList`, `gpsLightDuration`) are stripped from activity detail responses to keep them manageable.

### Region Handling
Regions (`eu`, `us`) map to different base URLs for both APIs. EU tokens only work on EU endpoints — mixing regions causes auth failures.

## Training plan → COROS

**COROS is the source of truth for the whole plan.** When the user asks for a plan change (run or strength — swap a session, adjust pace, move a test date, etc.), update the COROS calendar directly, and in the *same action* mirror that change into both Google Calendar and `training_plan.html`. Direction of flow is COROS → everything else, not the other way round.

- **COROS**: update directly via `workout_sync/sync.py` (`push_session`, `clear_scheduled_workouts`) / `coros_api.py`.
- **Google Calendar**: mirror the same change via `workout_sync/google_calendar.py` (`build_calendar_service`, `event_body`, matching `syncKey` = `date:workoutKey`) — create/update/delete just the affected day's event.
- **`training_plan.html`**: edit the corresponding day-row (day-note + run-cell text) so it stays an accurate **visual summary** of what's actually on COROS. It is not authoritative and nothing should read it to decide what's scheduled — it's for the user to glance at in a browser.

**Do not run the old HTML → COROS/Calendar push scripts** (`npm run sync:plan`, `npm run plan:serve` autosync, `coros-mcp calendar-sync`) to make plan changes — they do a full resync *from* the HTML, which is backwards from the current flow and will overwrite manual COROS/Calendar edits with stale HTML content. `scripts/sync-plan.sh` no longer calls `calendar-sync` for this reason (removed 2026-09-21). These scripts still exist for historical/bulk-import reasons but are not part of the normal "make a plan change" workflow anymore.
