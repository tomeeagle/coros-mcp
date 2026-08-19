"""Weekly schedules loaded from training_plan.html."""

from __future__ import annotations

from pathlib import Path

from workout_sync.plan_html import DEFAULT_PLAN_PATH, load_weeks, parse_plan_html


def _load() -> dict[str, dict]:
    if DEFAULT_PLAN_PATH.is_file():
        return load_weeks()
    return {}


WEEKS: dict[str, dict] = _load()

SCHEDULE: dict[str, list[str]] = {}
if DEFAULT_PLAN_PATH.is_file():
    _initial_plan = parse_plan_html()
    SCHEDULE.update({d: list(k) for d, k in _initial_plan.schedule.items()})
else:
    for _week in WEEKS.values():
        for day, keys in _week.get("days", {}).items():
            SCHEDULE[day] = list(keys) if isinstance(keys, list) else [keys]


def reload_schedules(html_path: Path | None = None) -> dict[str, dict]:
    """Re-read plan HTML (e.g. after editing training_plan.html)."""
    global WEEKS, SCHEDULE
    plan = parse_plan_html(html_path)
    WEEKS = {
        k: {"label": w.label, "days": dict(w.days)}
        for k, w in plan.weeks.items()
    }
    SCHEDULE.clear()
    SCHEDULE.update({d: list(k) for d, k in plan.schedule.items()})
    return WEEKS
