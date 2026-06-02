"""Push workouts to the COROS calendar."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import coros_api

from workout_sync import schedules as _schedules
from workout_sync.auth import ensure_auth
from workout_sync.plan_html import DEFAULT_PLAN_PATH, parse_plan_html
from workout_sync.schedules import SCHEDULE, WEEKS
from workout_sync.strength import build_strength_exercises
from workout_sync.workouts import WORKOUTS


def fmt_day(day_str: str) -> str:
    return datetime.strptime(day_str, "%Y%m%d").strftime("%a %d %b")


def resolve_schedule(
    *,
    week_keys: list[str] | None = None,
    days: dict[str, str] | None = None,
    upcoming_only: bool = True,
) -> dict[str, str]:
    """Build date -> workout_key from week keys, explicit days, or full SCHEDULE."""
    merged: dict[str, str] = {}

    weeks = _schedules.WEEKS
    if week_keys:
        for wk in week_keys:
            if wk not in weeks:
                raise KeyError(f"Unknown week: {wk}. Use list-weeks to see options.")
            merged.update(weeks[wk]["days"])
    elif days:
        merged = dict(days)
    else:
        merged = dict(SCHEDULE)

    if upcoming_only:
        today = date.today()
        merged = {
            k: v
            for k, v in merged.items()
            if datetime.strptime(k, "%Y%m%d").date() >= today
        }

    return dict(sorted(merged.items()))


def describe_session(day: str, workout_key: str) -> str:
    w = WORKOUTS.get(workout_key, {})
    return f"{fmt_day(day):12}  {w.get('name', workout_key)}"


async def push_session(auth: Any, day: str, workout_key: str) -> None:
    w = WORKOUTS.get(workout_key)
    if not w:
        raise KeyError(f"Unknown workout key: {workout_key}")

    kind = w.get("kind", "run")
    if kind == "strength":
        preset = w.get("strength_preset", "full_body")
        exercises = build_strength_exercises(preset)
        await coros_api.schedule_strength_workout(
            auth=auth,
            name=w["name"],
            exercises=exercises,
            happen_day=day,
            sets=int(w.get("circuit_sets", 1)),
        )
    else:
        await coros_api.schedule_workout(
            auth=auth,
            name=w["name"],
            steps=w["steps"],
            happen_day=day,
            sport_type=w.get("sport_type", 100),
            intensity_type=w.get("intensity_type", 0),
        )


def schedule_date_bounds(
    schedule: dict[str, str],
    *,
    padding_days: int = 7,
) -> tuple[str, str]:
    """YYYYMMDD range covering schedule keys with optional padding."""
    if not schedule:
        today = date.today()
        end = today + timedelta(days=90)
        return today.strftime("%Y%m%d"), end.strftime("%Y%m%d")
    keys = sorted(schedule.keys())
    start = datetime.strptime(keys[0], "%Y%m%d").date() - timedelta(days=padding_days)
    end = datetime.strptime(keys[-1], "%Y%m%d").date() + timedelta(days=padding_days)
    return start.strftime("%Y%m%d"), end.strftime("%Y%m%d")


async def full_resync(
    *,
    upcoming_only: bool = True,
    html_path: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Replace COROS calendar workouts with the current plan HTML:
    1) parse plan  2) delete existing sessions in range  3) push plan sessions.
    """
    path = html_path or DEFAULT_PLAN_PATH
    _schedules.reload_schedules(path)
    plan = parse_plan_html(path)

    schedule = resolve_schedule(upcoming_only=upcoming_only)
    clear_start, clear_end = schedule_date_bounds(plan.schedule)

    result: dict[str, Any] = {
        "plan_file": str(path),
        "upcoming_only": upcoming_only,
        "clear_range": f"{clear_start} – {clear_end}",
        "sessions_to_push": len(schedule),
        "removed": 0,
        "pushed": 0,
        "push_errors": 0,
        "messages": [],
    }

    if dry_run:
        result["messages"].append(f"[dry run] Would clear {clear_start}–{clear_end}")
        result["messages"].append(f"[dry run] Would push {len(schedule)} sessions")
        return result

    auth = await ensure_auth()
    removed, clear_logs = await coros_api.clear_scheduled_workouts(auth, clear_start, clear_end)
    result["removed"] = removed
    result["messages"].extend(clear_logs)

    pushed, errors, push_logs = await push_schedule(schedule, auth=auth)
    result["pushed"] = pushed
    result["push_errors"] = errors
    result["messages"].extend(push_logs)
    return result


async def push_schedule(
    schedule: dict[str, str],
    *,
    dry_run: bool = False,
    auth: Any | None = None,
) -> tuple[int, int, list[str]]:
    """Push all sessions. Returns (success, errors, error_messages)."""
    if dry_run:
        return len(schedule), 0, []

    if auth is None:
        auth = await ensure_auth()

    success = 0
    errors = 0
    messages: list[str] = []

    for day, key in schedule.items():
        w = WORKOUTS.get(key, {})
        label = w.get("name", key)
        try:
            await push_session(auth, day, key)
            success += 1
            messages.append(f"✓ {fmt_day(day)} — {label}")
        except Exception as exc:
            errors += 1
            messages.append(f"✗ {fmt_day(day)} — {label}: {exc}")

    return success, errors, messages
