"""Push workouts to the COROS calendar."""

from __future__ import annotations

import asyncio
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

_resync_lock = asyncio.Lock()


def fmt_day(day_str: str) -> str:
    return datetime.strptime(day_str, "%Y%m%d").strftime("%a %d %b")


def _is_run_workout_key(key: str) -> bool:
    return key.startswith(
        ("bac_", "tempo_", "easy_", "long_", "run_club_", "race_"),
    )


def _one_run_per_day(keys: list[str]) -> list[str]:
    """Hard cap: one run workout per day (strength sessions unchanged)."""
    runs = [k for k in keys if _is_run_workout_key(k)]
    if len(runs) <= 1:
        return keys
    non_runs = [k for k in keys if not _is_run_workout_key(k)]
    bac = [k for k in runs if k.startswith("bac_")]
    chosen = bac[0] if bac else runs[0]
    return non_runs + [chosen] if non_runs else [chosen]


def resolve_schedule(
    *,
    week_keys: list[str] | None = None,
    days: dict[str, str] | None = None,
    upcoming_only: bool = True,
) -> dict[str, list[str]]:
    """Build date -> workout keys from week keys, explicit days, or full SCHEDULE."""
    merged: dict[str, list[str]] = {}

    weeks = _schedules.WEEKS
    if week_keys:
        for wk in week_keys:
            if wk not in weeks:
                raise KeyError(f"Unknown week: {wk}. Use list-weeks to see options.")
            for day, keys in weeks[wk]["days"].items():
                merged[day] = list(keys) if isinstance(keys, list) else [keys]
    elif days:
        merged = {d: [k] if isinstance(k, str) else list(k) for d, k in days.items()}
    else:
        merged = {d: list(k) for d, k in SCHEDULE.items()}

    if upcoming_only:
        today = date.today()
        merged = {
            k: v
            for k, v in merged.items()
            if datetime.strptime(k, "%Y%m%d").date() >= today
        }

    return dict(sorted(merged.items()))


def describe_session(day: str, workout_keys: str | list[str]) -> str:
    keys = [workout_keys] if isinstance(workout_keys, str) else list(workout_keys)
    names = [WORKOUTS.get(k, {}).get("name", k) for k in keys]
    return f"{fmt_day(day):12}  {' + '.join(names)}"


async def push_session(
    auth: Any,
    day: str,
    workout_key: str,
    *,
    sort_no: int = 1,
) -> None:
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
            sort_no=sort_no,
        )
    else:
        await coros_api.schedule_run_workout(
            auth=auth,
            name=w["name"],
            steps=w["steps"],
            happen_day=day,
            sort_no=sort_no,
        )


def schedule_date_bounds(
    schedule: dict[str, list[str]],
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
    clear_start, clear_end = schedule_date_bounds(schedule)

    result: dict[str, Any] = {
        "plan_file": str(path),
        "upcoming_only": upcoming_only,
        "clear_range": f"{clear_start} – {clear_end}",
        "sessions_to_push": sum(len(k) for k in schedule.values()),
        "removed": 0,
        "pushed": 0,
        "push_errors": 0,
        "messages": [],
        "calendar_plan": {},
    }

    if dry_run:
        result["messages"].append(f"[dry run] Would clear {clear_start}–{clear_end}")
        n = sum(len(_one_run_per_day(k)) for k in schedule.values())
        result["messages"].append(f"[dry run] Would push {n} sessions")
        return result

    async with _resync_lock:
        auth = await ensure_auth()
        try:
            result["calendar_plan"] = await coros_api.fetch_active_calendar_plan(
                auth, start_day=clear_start, end_day=clear_end,
            )
        except Exception:
            result["calendar_plan"] = {}
        removed, clear_logs = await coros_api.clear_scheduled_workouts(
            auth, clear_start, clear_end,
        )
        result["removed"] = removed
        result["messages"].extend(clear_logs)

        pushed, errors, push_logs = await push_schedule(
            schedule, auth=auth, clear_each_day=False,
        )
        result["pushed"] = pushed
        result["push_errors"] = errors
        result["messages"].extend(push_logs)
    return result


async def push_schedule(
    schedule: dict[str, list[str]],
    *,
    dry_run: bool = False,
    auth: Any | None = None,
    clear_each_day: bool = True,
) -> tuple[int, int, list[str]]:
    """Push all sessions. Returns (success, errors, error_messages).

    When clear_each_day is True (default), removes existing calendar workouts on
    each day before pushing — prevents duplicates from repeat push/sync.
    """
    total = sum(len(_one_run_per_day(k)) for k in schedule.values())
    if dry_run:
        return total, 0, []

    if auth is None:
        auth = await ensure_auth()

    success = 0
    errors = 0
    messages: list[str] = []

    for day, keys in schedule.items():
        keys = _one_run_per_day(keys)
        if clear_each_day:
            removed, _ = await coros_api.clear_scheduled_workouts(auth, day, day)
            if removed:
                messages.append(f"Cleared {removed} on {fmt_day(day)}")
        for sort_no, key in enumerate(keys, start=1):
            w = WORKOUTS.get(key, {})
            label = w.get("name", key)
            try:
                await push_session(auth, day, key, sort_no=sort_no)
                success += 1
                suffix = f" (#{sort_no})" if len(keys) > 1 else ""
                messages.append(f"✓ {fmt_day(day)} — {label}{suffix}")
            except Exception as exc:
                errors += 1
                messages.append(f"✗ {fmt_day(day)} — {label}: {exc}")

    return success, errors, messages
