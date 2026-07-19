"""CLI commands for Coros MCP Server."""
import asyncio
import getpass
import sys
import time

from auth.storage import clear_token, get_token, is_keyring_available
from coros_api import TOKEN_TTL_MS, get_stored_auth, login, login_mobile, try_auto_login


def _prompt_credentials() -> tuple[str, str, str]:
    """Prompt for email, password, and region. Returns (email, password, region)."""
    email = input("Email: ").strip()
    if not email:
        print("Error: email is required.")
        sys.exit(1)

    password = getpass.getpass("Password: ")
    if not password:
        print("Error: password is required.")
        sys.exit(1)

    print()
    print("Region options: eu, us, asia")
    region = input("Region [eu]: ").strip().lower() or "eu"
    if region not in ("eu", "us", "asia"):
        print(f"Warning: unknown region '{region}', using it anyway.")
    return email, password, region


def cmd_auth() -> int:
    """Authenticate with Coros credentials and store token in keyring."""
    print("Coros MCP — Authentication")
    print()

    if is_keyring_available():
        print("Token will be stored in your system keyring.")
    else:
        print("System keyring not available — token will be stored in an encrypted local file.")
    print()

    email, password, region = _prompt_credentials()
    print()
    print("Authenticating…")
    try:
        auth = asyncio.run(login(email, password, region, skip_mobile=False))
        print(f"✓ Authenticated as user {auth.user_id} (region: {auth.region})")
        print("  Token stored securely. You only need to do this once.")
        return 0
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        return 1


def cmd_auth_web() -> int:
    """Authenticate with Coros web API only (no mobile token)."""
    print("Coros MCP — Web API Authentication")
    print()

    email, password, region = _prompt_credentials()
    print()
    print("Authenticating (web only)…")
    try:
        auth = asyncio.run(login(email, password, region, skip_mobile=True))
        print(f"✓ Web API authenticated as user {auth.user_id} (region: {auth.region})")
        print("  Mobile token skipped — sleep data will not be available.")
        return 0
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        return 1


def cmd_auth_mobile() -> int:
    """Authenticate with Coros mobile API only."""
    print("Coros MCP — Mobile API Authentication")
    print()

    email, password, region = _prompt_credentials()
    print()
    print("Authenticating (mobile only)…")
    try:
        auth = asyncio.run(login_mobile(email, password, region))
        print(f"✓ Mobile API authenticated (region: {auth.region})")
        print("  Sleep data is now available.")
        return 0
    except Exception as e:
        print(f"✗ Mobile authentication failed: {e}")
        return 1


def cmd_auth_status() -> int:
    """Check whether valid tokens are stored."""
    auth = get_stored_auth()
    if auth is None:
        auth = asyncio.run(try_auto_login())
    if auth:
        age_ms = int(time.time() * 1000) - auth.timestamp
        remaining_hours = round((TOKEN_TTL_MS - age_ms) / 3_600_000, 1)

        # Web token status
        if auth.access_token:
            print(f"✓ Web API    — user_id: {auth.user_id}, region: {auth.region}, expires in ~{remaining_hours}h")
        else:
            print("✗ Web API    — not authenticated")

        # Mobile token status
        if auth.mobile_access_token:
            print("✓ Mobile API — token present (sleep data available)")
        elif auth.mobile_login_payload:
            print("⚠ Mobile API — token expired (can auto-refresh)")
        else:
            print("✗ Mobile API — not authenticated (run 'coros-mcp auth' or 'coros-mcp auth-mobile')")

        return 0
    else:
        result = get_token()
        if result.success:
            print("⚠ Token found but may be expired. Run 'coros-mcp auth' to re-authenticate.")
        else:
            print("✗ Not authenticated. Run 'coros-mcp auth' to log in.")
        return 1


def cmd_auth_clear() -> int:
    """Remove stored token from all backends."""
    result = clear_token()
    if result.success:
        print("✓ Token cleared.")
        return 0
    else:
        print(f"✗ {result.message}")
        return 1


def cmd_sync() -> int:
    """Full historical sync: pull all data from Coros and store locally."""
    import argparse
    from datetime import datetime, timedelta

    from cache.sync import sync_all

    parser = argparse.ArgumentParser(
        prog="coros-mcp sync",
        description="Sync Coros data to the local cache.",
    )
    parser.add_argument(
        "--from",
        dest="start_day",
        metavar="YYYYMMDD",
        help="First date to sync (default: 2 years ago)",
    )
    parser.add_argument(
        "--to",
        dest="end_day",
        metavar="YYYYMMDD",
        help="Last date to sync (default: today)",
    )
    parsed = parser.parse_args(sys.argv[2:])
    start_day = parsed.start_day or (datetime.now() - timedelta(days=730)).strftime("%Y%m%d")
    end_day = parsed.end_day

    auth = get_stored_auth()
    if auth is None:
        auth = asyncio.run(try_auto_login())
    if auth is None:
        print("✗ Not authenticated. Set COROS_EMAIL and COROS_PASSWORD in .env, or run 'coros-mcp auth'.")
        return 1

    range_str = f"{start_day} → {end_day}" if end_day else f"{start_day} → today"
    print(f"Coros MCP — Sync ({range_str})")
    print("This may take a few minutes for a large date range.")
    print()

    async def _run():
        async def on_progress(msg: str):
            print(f"  {msg}")

        return await sync_all(auth, start_day, end_day=end_day, on_progress=on_progress)

    try:
        stats = asyncio.run(_run())
        print()
        print("✓ Sync complete")
        print(f"  Daily records : {stats['daily']}")
        print(f"  Sleep records : {stats['sleep']}")
        print(f"  Activities    : {stats['activities']}")
        if stats["errors"]:
            print(f"  Errors        : {len(stats['errors'])}")
            for e in stats["errors"]:
                print(f"    - {e}")
        c = stats.get("cache", {})
        print()
        print("Cache coverage:")
        for key in ("daily_records", "sleep_records", "activities"):
            s = c.get(key, {})
            print(f"  {key:16s}: {s.get('count', 0)} records  [{s.get('from', '—')} → {s.get('to', '—')}]")
        return 0
    except Exception as e:
        print(f"✗ Sync failed: {e}")
        return 1


def cmd_cache_status() -> int:
    """Show local cache coverage."""
    from cache.store import cache_status, init_db
    init_db()
    c = cache_status()
    print(f"Cache: {c['db_path']}")
    print()
    for key in ("daily_records", "sleep_records", "activities"):
        s = c[key]
        if s["count"]:
            print(f"  {key:16s}: {s['count']:5d} records  [{s['from']} → {s['to']}]")
        else:
            print(f"  {key:16s}:     0 records  (empty — run 'coros-mcp sync')")
    return 0


def cmd_runs() -> int:
    """List runs from local cache (fast). Use --refresh to pull latest from Coros first."""
    import argparse
    from datetime import datetime, timedelta

    from cache.store import get_activities, init_db
    from cache.sync import fetch_activities_cached
    from cache.utils import LOCAL_TZ

    parser = argparse.ArgumentParser(
        prog="coros-mcp runs",
        description="List runs from local cache (milliseconds).",
    )
    parser.add_argument("--from", dest="start_day", metavar="YYYYMMDD", help="Start date")
    parser.add_argument("--to", dest="end_day", metavar="YYYYMMDD", help="End date (default: today)")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Fetch latest from Coros into cache before listing (~1–2s)",
    )
    parsed = parser.parse_args(sys.argv[2:])

    today = datetime.now(tz=LOCAL_TZ).date() if LOCAL_TZ else datetime.now().date()
    end_day = parsed.end_day or today.strftime("%Y%m%d")
    start_day = parsed.start_day or (today - timedelta(days=6)).strftime("%Y%m%d")

    init_db()
    if parsed.refresh:
        auth = get_stored_auth() or asyncio.run(try_auto_login())
        if auth is None:
            print("✗ Not authenticated. Run 'coros-mcp auth' or use cache-only (omit --refresh).")
            return 1
        asyncio.run(fetch_activities_cached(auth, start_day, end_day, size=100))

    runs = [
        a for a in get_activities(start_day, end_day)
        if a.sport_type in {1, 100, 101, 102, 103}
        or "run" in (a.sport_name or "").lower()
    ]
    runs.sort(key=lambda a: int(a.start_time or 0))

    if not runs:
        print(f"No runs in cache for {start_day}–{end_day}.")
        print("Run: coros-mcp sync --from", start_day, "--to", end_day)
        return 0

    total_km = 0.0
    print(f"Runs {start_day}–{end_day} (from cache):\n")
    for a in runs:
        km = (a.distance_meters or 0) / 1000
        total_km += km
        dur = (a.duration_seconds or 0) / 60
        pace = dur / km if km > 0.5 else 0
        if a.start_time and LOCAL_TZ:
            day = datetime.fromtimestamp(int(a.start_time), tz=LOCAL_TZ).strftime("%a %d")
        else:
            day = "?"
        print(
            f"  {day}  {a.name or 'Run':28}  {km:4.1f}km  {dur:3.0f}min  "
            f"{pace:4.1f}/km  HR {a.avg_hr or '—'}  load {a.training_load or '—'}"
        )
    print(f"\n  {len(runs)} runs · {total_km:.1f}km total")
    return 0


def cmd_export_calendar() -> int:
    """Export plan to plan_calendar_export.json for Google Calendar."""
    from workout_sync.export_calendar import export_calendar_json

    path = export_calendar_json()
    print(f"✓ Exported {path.name} ({path.stat().st_size:,} bytes)")
    return 0


def cmd_calendar_auth() -> int:
    """Authenticate direct Google Calendar access using installed-app OAuth."""
    import argparse

    from workout_sync.google_calendar import authenticate_google_calendar

    parser = argparse.ArgumentParser(
        prog="coros-mcp calendar-auth",
        description="Connect Google Calendar using a Desktop app OAuth client.",
    )
    parser.add_argument("--force", action="store_true", help="Repeat OAuth even if a token exists")
    parsed = parser.parse_args(sys.argv[2:])
    try:
        token_path = authenticate_google_calendar(force=parsed.force)
        print("✓ Google Calendar connected")
        print(f"  Token stored securely: {token_path}")
        return 0
    except Exception as e:
        print(f"✗ Google Calendar authentication failed: {e}")
        return 1


def cmd_calendar_sync() -> int:
    """Reconcile Google Calendar with the exported training plan."""
    import argparse

    from workout_sync.google_calendar import sync_google_calendar

    parser = argparse.ArgumentParser(
        prog="coros-mcp calendar-sync",
        description="Sync project-managed training events to Google Calendar.",
    )
    parser.add_argument("--calendar-id", help="Calendar ID (default: GOOGLE_CALENDAR_ID or primary)")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    parsed = parser.parse_args(sys.argv[2:])
    try:
        result = sync_google_calendar(
            calendar_id=parsed.calendar_id,
            dry_run=parsed.dry_run,
        )
        prefix = "Would sync" if parsed.dry_run else "✓ Google Calendar synced"
        print(prefix)
        print(
            f"  Created {result.created} · Updated {result.updated} · "
            f"Deleted {result.deleted} · Unchanged {result.unchanged}"
        )
        return 0
    except Exception as e:
        print(f"✗ Google Calendar sync failed: {e}")
        return 1


def cmd_weekly_api() -> int:
    """Start the local weekly coach HTTP API for the Next.js UI."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="coros-mcp weekly-api",
        description="Serve the weekly coach review API on localhost.",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5055)
    parsed = parser.parse_args(sys.argv[2:])
    try:
        from workout_sync.activity_api import main as weekly_main

        weekly_main(host=parsed.host, port=parsed.port)
        return 0
    except ImportError:
        print("✗ Flask is required. Install with: pip install -e '.[sync]'")
        return 1
    except Exception as e:
        print(f"✗ weekly-api failed: {e}")
        return 1


def cmd_serve() -> int:
    """Start the MCP server (stdio mode)."""
    import server
    server.main()
    return 0


def cmd_help() -> int:
    print(
        """Coros MCP Server — CLI

Usage:
  coros-mcp serve                   Start the MCP server (used by Claude Code / OpenClaw)
  coros-mcp auth                    Authenticate with your Coros account (web + mobile)
  coros-mcp auth-web                Authenticate web API only (no sleep data)
  coros-mcp auth-mobile             Authenticate mobile API only (sleep data)
  coros-mcp auth-status             Check status of both tokens
  coros-mcp auth-clear              Remove stored token
  coros-mcp sync [--from YYYYMMDD] [--to YYYYMMDD]  Sync to local cache (default: 2 years → today)
  coros-mcp runs [--from YYYYMMDD] [--to YYYYMMDD] [--refresh]  List runs from cache (fast)
  coros-mcp export-calendar          Export plan_calendar_export.json for GCal
  coros-mcp calendar-auth [--force]  Connect Google Calendar using OAuth
  coros-mcp calendar-sync [--dry-run] [--calendar-id ID]  Sync plan events to Google Calendar
  coros-mcp weekly-api [--port 5055]  Local weekly coach API for the Next.js UI
  coros-mcp cache-status            Show local cache coverage
  coros-mcp help                    Show this help message
"""
    )
    return 0


def main() -> None:
    from dotenv import load_dotenv
    load_dotenv()

    command = sys.argv[1] if len(sys.argv) > 1 else "help"
    commands = {
        "serve": cmd_serve,
        "auth": cmd_auth,
        "auth-web": cmd_auth_web,
        "auth-mobile": cmd_auth_mobile,
        "auth-status": cmd_auth_status,
        "auth-clear": cmd_auth_clear,
        "sync": cmd_sync,
        "runs": cmd_runs,
        "export-calendar": cmd_export_calendar,
        "calendar-auth": cmd_calendar_auth,
        "calendar-sync": cmd_calendar_sync,
        "weekly-api": cmd_weekly_api,
        "cache-status": cmd_cache_status,
        "help": cmd_help,
        "--help": cmd_help,
        "-h": cmd_help,
    }
    if command in commands:
        sys.exit(commands[command]())
    else:
        print(f"Unknown command: {command}")
        print("Run 'coros-mcp help' for usage.")
        sys.exit(1)


if __name__ == "__main__":
    main()
