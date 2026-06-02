#!/usr/bin/env python3
"""
COROS Workout Sync — Tom's Training Plan

  cp .env.example .env          # COROS_EMAIL, COROS_PASSWORD, COROS_REGION
  npm run sync:setup            # once: venv + pip install
  npm run plan:serve            # view plan_v1_8.html in the browser
  npm run sync:web              # edit plan → click Sync to COROS
  npm run sync                  # full resync from terminal

  python coros_sync.py import-plan
  python coros_sync.py push --week week_5
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from workout_sync import schedules as sched_mod
from workout_sync.auth import auth_status_message, load_dotenv
from workout_sync.plan_html import DEFAULT_PLAN_PATH, parse_plan_html
from workout_sync.sync import describe_session, full_resync, push_schedule, resolve_schedule
from workout_sync.workouts import WORKOUTS

load_dotenv()
sched_mod.reload_schedules()


def _weeks() -> dict:
    return sched_mod.WEEKS


def cmd_list_weeks() -> None:
    print("\nAvailable weeks:\n")
    for key, week in _weeks().items():
        n = len(week["days"])
        print(f"  {key:12}  {week['label']}  ({n} sessions)")
    print()


def cmd_list_workouts() -> None:
    print("\nWorkout keys:\n")
    for key, w in sorted(WORKOUTS.items()):
        kind = w.get("kind", "run")
        print(f"  {key:22}  [{kind:8}]  {w['name']}")
    print(f"\n  Plan: {DEFAULT_PLAN_PATH.name}")
    print(f"  Auth: {auth_status_message()}\n")


def cmd_import_plan(args: argparse.Namespace) -> int:
    path = Path(args.plan) if args.plan else DEFAULT_PLAN_PATH
    if not path.is_file():
        print(f"❌ Plan not found: {path}")
        return 1

    plan = parse_plan_html(path)
    sched_mod.reload_schedules(path)

    n_sessions = sum(len(keys) for keys in plan.schedule.values())
    print(f"\n📄 {path.name} — {len(plan.weeks)} weeks, {n_sessions} syncable sessions\n")
    for wk in plan.weeks.values():
        print(f"  {wk.key:28}  {wk.label}")
        for day, keys in sorted(wk.days.items()):
            if isinstance(keys, str):
                keys = [keys]
            names = [WORKOUTS.get(k, {}).get("name", k) for k in keys]
            print(f"    {day}  {' + '.join(names)}")

    if plan.unmapped:
        print(f"\n⚠️  {len(plan.unmapped)} unmapped (not pushed to COROS):")
        for d in plan.unmapped:
            print(f"    {d.yyyymmdd}  {d.day_label}: {d.run_text[:70]}")

    print("\nSchedules reloaded — use push --week <key> or web UI.")
    return 0


async def cmd_sync(args: argparse.Namespace) -> int:
    print("\n🏃 COROS Workout Sync — full replace")
    print("=" * 45)
    print(f"Auth: {auth_status_message()}\n")

    if not args.yes:
        schedule = resolve_schedule(upcoming_only=not args.all_dates)
        n = sum(len(k) for k in schedule.values())
        print(f"Will clear calendar in plan range, then push {n} session(s):\n")
        for day, keys in schedule.items():
            print(f"  {describe_session(day, keys)}")
        print()
        confirm = input("Continue? (y/n): ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return 0

    try:
        result = await full_resync(upcoming_only=not args.all_dates)
    except Exception as exc:
        print(f"❌ {exc}")
        return 1

    print(f"Cleared range: {result['clear_range']}")
    print(f"Removed {result['removed']} · Pushed {result['pushed']}")
    if result["push_errors"]:
        print(f"⚠️  {result['push_errors']} push error(s)")
    for line in result["messages"][-20:]:
        print(f"  {line}")
    print("\nOpen COROS app → Training Plan → sync to watch.")
    return 1 if result["push_errors"] else 0


async def cmd_push(args: argparse.Namespace) -> int:
    try:
        schedule = resolve_schedule(
            week_keys=args.week or None,
            upcoming_only=not args.all_dates,
        )
    except KeyError as exc:
        print(f"❌ {exc}")
        return 1

    if not schedule:
        print("No sessions to sync.")
        return 0

    print("\n🏃 COROS Workout Sync")
    print("=" * 45)
    n = sum(len(k) for k in schedule.values())
    print(f"\nSessions ({n}):\n")
    for day, keys in schedule.items():
        print(f"  {describe_session(day, keys)}")

    if not args.yes:
        print()
        confirm = input("Push to COROS? (y/n): ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return 0

    print()
    success, errors, messages = await push_schedule(schedule)
    for line in messages:
        print(f"  {line}")

    print(f"\n{'=' * 45}")
    print(f"✓ {success} synced")
    if errors:
        print(f"⚠️  {errors} failed")
    print("\nOpen COROS app → Training Plan, then sync to your watch.")
    return 1 if errors else 0


def cmd_web(args: argparse.Namespace) -> int:
    try:
        from workout_sync.web import run_server
    except ImportError:
        print("Flask required: pip install flask")
        return 1
    run_server(host=args.host, port=args.port)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Push Tom's training plan to COROS")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list-weeks", help="Show week keys for --week")
    sub.add_parser("list-workouts", help="Show workout keys")

    imp_p = sub.add_parser("import-plan", help="Parse plan HTML and show generated schedule")
    imp_p.add_argument("--plan", help="Path to plan HTML (default: plan_v1_8.html)")

    sync_p = sub.add_parser(
        "sync",
        help="Clear calendar in plan range, then push sessions from plan HTML",
    )
    sync_p.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")
    sync_p.add_argument("--all-dates", action="store_true", help="Include past dates")

    push_p = sub.add_parser("push", help="Push sessions only (no clear) — prefer 'sync'")
    push_p.add_argument("--week", action="append", help="Week key (repeatable)")
    push_p.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")
    push_p.add_argument("--all-dates", action="store_true", help="Include past dates")

    web_p = sub.add_parser("web", help="Local web UI to pick weeks and push")
    web_p.add_argument("--host", default="127.0.0.1")
    web_p.add_argument("--port", type=int, default=5055)

    args = parser.parse_args()

    if args.command == "list-weeks":
        cmd_list_weeks()
        return 0
    if args.command == "list-workouts":
        cmd_list_workouts()
        return 0
    if args.command == "import-plan":
        return cmd_import_plan(args)
    if args.command == "sync":
        return asyncio.run(cmd_sync(args))
    if args.command == "web":
        return cmd_web(args)
    if args.command == "push":
        return asyncio.run(cmd_push(args))

    # Default: interactive push of all upcoming
    args.command = "push"
    args.week = None
    args.yes = False
    args.all_dates = False
    return asyncio.run(cmd_push(args))


if __name__ == "__main__":
    raise SystemExit(main())
