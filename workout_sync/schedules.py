"""Weekly schedules loaded from plan_v1_8.html."""

from __future__ import annotations

from pathlib import Path

from workout_sync.plan_html import DEFAULT_PLAN_PATH, load_weeks


def _load() -> dict[str, dict]:
    if DEFAULT_PLAN_PATH.is_file():
        return load_weeks()
    return {}


WEEKS: dict[str, dict] = _load()

SCHEDULE: dict[str, str] = {}
for _week in WEEKS.values():
    SCHEDULE.update(_week.get("days", {}))


def reload_schedules(html_path: Path | None = None) -> dict[str, dict]:
    """Re-read plan HTML (e.g. after editing plan_v1_8.html)."""
    global WEEKS, SCHEDULE
    WEEKS = load_weeks(html_path)
    SCHEDULE.clear()
    for week in WEEKS.values():
        SCHEDULE.update(week.get("days", {}))
    return WEEKS
