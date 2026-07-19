"""Rule-based weekly coach: Coros activities vs training_plan.html."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import Any

from cache.store import get_activities, get_daily_records, init_db
from models import ActivitySummary
from workout_sync.plan_html import parse_plan_html
from workout_sync.workouts import WORKOUTS

# Sport types treated as running for volume / HR comparisons
_RUN_SPORTS = {1, 100, 101, 102, 103}
_HARD_KEYS = ("bac_", "progression_", "tempo_", "build_", "race_")


@dataclass
class DayReview:
    date: str
    planned: str | None
    done: str | None
    status: str  # matched | missed | extra | rest | optional_skip


@dataclass
class Suggestion:
    date: str  # YYYYMMDD
    from_label: str
    to_label: str
    reason: str


@dataclass
class WeekReview:
    week_start: str  # ISO date Monday
    week_end: str
    headline: str
    notes: list[str] = field(default_factory=list)
    days: list[DayReview] = field(default_factory=list)
    next_week_suggestions: list[Suggestion] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "weekStart": self.week_start,
            "weekEnd": self.week_end,
            "headline": self.headline,
            "notes": self.notes,
            "days": [asdict(d) for d in self.days],
            "nextWeekSuggestions": [
                {
                    "date": s.date,
                    "from": s.from_label,
                    "to": s.to_label,
                    "reason": s.reason,
                }
                for s in self.next_week_suggestions
            ],
            "stats": self.stats,
        }


def monday_of(d: date) -> date:
    return d - timedelta(days=d.weekday())


def week_bounds(week: str | None = None) -> tuple[date, date]:
    """week: YYYYMMDD or YYYY-MM-DD anywhere in the week; default = this week."""
    if week:
        raw = week.replace("-", "")
        anchor = datetime.strptime(raw, "%Y%m%d").date()
    else:
        anchor = datetime.now(UTC).astimezone().date()
    start = monday_of(anchor)
    return start, start + timedelta(days=6)


def _ymd(d: date) -> str:
    return d.strftime("%Y%m%d")


def _iso(d: date) -> str:
    return d.isoformat()


def _activity_day(a: ActivitySummary) -> str | None:
    if a.start_time and str(a.start_time).isdigit():
        return datetime.fromtimestamp(int(a.start_time), tz=UTC).strftime("%Y%m%d")
    return None


def _is_run(a: ActivitySummary) -> bool:
    if a.sport_type in _RUN_SPORTS:
        return True
    name = (a.sport_name or "").lower()
    return "run" in name


def _planned_km(keys: list[str]) -> float:
    total = 0.0
    for k in keys:
        w = WORKOUTS.get(k, {})
        steps = w.get("steps") or []
        for s in steps:
            if "distance_meters" in s:
                total += s["distance_meters"] / 1000
            elif "target_distance_meters" in s:
                total += s["target_distance_meters"] / 1000
        # crude fallback from key name
        m = re.search(r"(\d+)k", k)
        if total == 0 and m and k.startswith(("easy_", "long_", "run_club_", "progression_")):
            total += float(m.group(1))
    return total


def _label_for_keys(keys: list[str]) -> str:
    parts = []
    for k in keys:
        w = WORKOUTS.get(k)
        parts.append(w["name"] if w else k)
    return " · ".join(parts)


def _is_hard_key(k: str) -> bool:
    return k.startswith(_HARD_KEYS)


def _is_optional_note(note: str) -> bool:
    return bool(re.search(r"optional\s+(BAC|PFTC)", note or "", re.I))


def _day_plan_labels(plan_schedule: dict[str, list[str]], ymd: str) -> list[str]:
    return list(plan_schedule.get(ymd, []))


def build_week_review(week: str | None = None, *, refresh: bool = False) -> WeekReview:
    """Build coach review for Mon–Sun week. refresh reserved for API live fetch."""
    _ = refresh  # live refresh handled by caller before invoking
    init_db()
    start, end = week_bounds(week)
    start_s, end_s = _ymd(start), _ymd(end)

    plan = parse_plan_html()
    schedule = plan.schedule

    activities = get_activities(start_s, end_s)
    by_day: dict[str, list[ActivitySummary]] = {}
    for a in activities:
        day = _activity_day(a)
        if not day:
            continue
        by_day.setdefault(day, []).append(a)

    daily = {d.date: d for d in get_daily_records(start_s, end_s)}

    # Collect optional notes from HTML via parse — use plan days only; optional from unmapped notes
    # Re-parse week notes from schedule keys only; optional BAC/PFTC inferred from workout keys absence
    # when day has easy default — check export isn't needed; use day status heuristics.

    days: list[DayReview] = []
    planned_run_km = 0.0
    done_run_km = 0.0
    missed_hard = 0
    missed_easy = 0
    extras: list[str] = []
    high_hr_notes: list[str] = []
    hard_done = 0
    mtb_minutes = 0

    # Recent easy-run HR baseline (prior 28 days ending before week)
    hist_start = _ymd(start - timedelta(days=28))
    hist_end = _ymd(start - timedelta(days=1))
    hist = [a for a in get_activities(hist_start, hist_end) if _is_run(a) and a.avg_hr]
    easy_hrs = [a.avg_hr for a in hist if a.avg_hr and (a.distance_meters or 0) < 12000]
    baseline_hr = (sum(easy_hrs) / len(easy_hrs)) if easy_hrs else None

    for i in range(7):
        d = start + timedelta(days=i)
        ymd = _ymd(d)
        keys = _day_plan_labels(schedule, ymd)
        planned_label = _label_for_keys(keys) if keys else None
        acts = by_day.get(ymd, [])
        done_bits = []
        for a in acts:
            km = (a.distance_meters or 0) / 1000
            mins = (a.duration_seconds or 0) / 60
            bit = a.name or a.sport_name or "Activity"
            if km >= 0.3:
                bit += f" · {km:.1f}km"
            elif mins >= 1:
                bit += f" · {mins:.0f}min"
            if a.avg_hr:
                bit += f" · HR {a.avg_hr}"
            done_bits.append(bit)
            if _is_run(a):
                done_run_km += km
                if baseline_hr and a.avg_hr and a.avg_hr >= baseline_hr + 12 and km >= 3:
                    high_hr_notes.append(
                        f"Heart rate looked high on {_friendly_day(d)}'s "
                        f"{(a.name or 'run').lower()} (avg {a.avg_hr} vs ~{baseline_hr:.0f} easy baseline)."
                    )
            sport = (a.sport_name or "").lower()
            if "mtb" in sport or "bike" in sport or (a.sport_type or 0) in {200, 201, 202, 204}:
                mtb_minutes += (a.duration_seconds or 0) / 60

        done_label = " · ".join(done_bits) if done_bits else None
        planned_run_km += _planned_km(keys)

        if not keys and not acts:
            status = "rest"
        elif keys and not acts:
            if any(k.startswith("strength_") for k in keys) and not any(
                k.startswith(("easy_", "long_", "bac_", "run_club_", "progression_")) for k in keys
            ):
                status = "missed"  # strength-only day with nothing logged
            else:
                # Optional BAC/PFTC days still have easy_* planned — missed if no activity
                status = "missed"
                if any(_is_hard_key(k) for k in keys):
                    missed_hard += 1
                else:
                    missed_easy += 1
        elif not keys and acts:
            status = "extra"
            extras.append(_friendly_day(d))
        else:
            status = "matched"
            if any(_is_hard_key(k) for k in keys):
                hard_done += 1

        days.append(
            DayReview(
                date=_iso(d),
                planned=planned_label,
                done=done_label,
                status=status,
            )
        )

    notes: list[str] = []
    suggestions: list[Suggestion] = []
    load_vals = [daily[k].training_load for k in daily if daily[k].training_load]
    week_load = sum(load_vals) if load_vals else 0

    hard_flags = 0
    if done_run_km > planned_run_km * 1.25 and planned_run_km >= 8:
        hard_flags += 1
        notes.append(
            f"Running volume was {done_run_km:.0f}km vs about {planned_run_km:.0f}km planned."
        )
    if mtb_minutes >= 90:
        hard_flags += 1
        notes.append(f"Solid bike time this week (~{mtb_minutes:.0f} min) — that counts toward load.")
    if week_load >= 80:
        hard_flags += 1
        notes.append(f"Training load stacked up ({week_load}).")

    for n in high_hr_notes[:2]:
        notes.append(n)
        hard_flags += 1

    if missed_easy + missed_hard >= 2:
        notes.append(f"You missed {missed_easy + missed_hard} planned sessions.")
    elif missed_easy + missed_hard == 1:
        notes.append("One planned session was skipped.")

    if extras:
        notes.append(f"Extra sessions on {', '.join(extras)}.")

    # Headline
    if hard_flags >= 2 or (done_run_km >= planned_run_km * 1.35 and planned_run_km >= 10):
        headline = "You went a bit hard this week."
        soften = True
    elif missed_easy + missed_hard >= 3 or done_run_km < planned_run_km * 0.55 and planned_run_km >= 10:
        headline = "This week was lighter than planned."
        soften = False
    elif missed_easy + missed_hard == 0 and abs(done_run_km - planned_run_km) <= max(3, planned_run_km * 0.2):
        headline = "Nice — you stayed about on track."
        soften = False
    else:
        headline = "Decent week — a few things to tidy up."
        soften = hard_flags >= 1

    if not notes:
        notes.append("No big red flags from the data we have.")

    # Next week suggestions
    next_start = end + timedelta(days=1)
    next_keys_by_day = {
        _ymd(next_start + timedelta(days=i)): schedule.get(_ymd(next_start + timedelta(days=i)), [])
        for i in range(7)
    }

    if soften:
        # Find first progression/tempo/bac in next week → ease to Easy 5K
        for ymd, keys in next_keys_by_day.items():
            for k in keys:
                if k.startswith(("progression_", "tempo_", "bac_", "build_")):
                    suggestions.append(
                        Suggestion(
                            date=ymd,
                            from_label=_label_for_keys([k]),
                            to_label="Easy 5K",
                            reason="Ease quality after a harder week.",
                        )
                    )
                    break
            if suggestions:
                break
        # Cap long run if present and long
        for ymd, keys in next_keys_by_day.items():
            for k in keys:
                if k.startswith("long_") and k not in ("long_10k",) and re.search(r"1[2-9]k|long_1[2-9]", k):
                    suggestions.append(
                        Suggestion(
                            date=ymd,
                            from_label=_label_for_keys([k]),
                            to_label="Long run 10K easy",
                            reason="Keep the long easy and capped while you settle.",
                        )
                    )
                    break
            if len(suggestions) >= 2:
                break
    elif missed_easy + missed_hard >= 2:
        # Don't stack quality if consistency is shaky
        for ymd, keys in next_keys_by_day.items():
            for k in keys:
                if k.startswith(("progression_", "bac_")):
                    suggestions.append(
                        Suggestion(
                            date=ymd,
                            from_label=_label_for_keys([k]),
                            to_label="Easy 5K",
                            reason="Prioritise showing up easy before adding intensity.",
                        )
                    )
                    break
            if suggestions:
                break

    return WeekReview(
        week_start=_iso(start),
        week_end=_iso(end),
        headline=headline,
        notes=notes[:6],
        days=days,
        next_week_suggestions=suggestions[:3],
        stats={
            "plannedRunKm": round(planned_run_km, 1),
            "doneRunKm": round(done_run_km, 1),
            "weekLoad": week_load,
            "mtbMinutes": round(mtb_minutes),
            "activityCount": len(activities),
        },
    )


def _friendly_day(d: date) -> str:
    return d.strftime("%A")


def apply_suggestions(suggestions: list[dict[str, str]]) -> dict[str, Any]:
    """Rewrite run-cell text in training_plan.html for suggestion dates; sync calendars."""
    from pathlib import Path

    from workout_sync.export_calendar import export_calendar_json
    from workout_sync.plan_html import DEFAULT_PLAN_PATH

    path: Path = DEFAULT_PLAN_PATH
    html = path.read_text(encoding="utf-8")
    changed = 0

    for s in suggestions:
        to_label = s["to"]
        from_label = (s.get("from") or "").strip()
        if not from_label:
            continue
        pattern = re.compile(
            rf'(<span class="run-cell[^"]*">)\s*{re.escape(from_label)}\s*(</span>)',
            re.I,
        )
        html, n = pattern.subn(rf"\g<1>{to_label}\g<2>", html, count=1)
        changed += n

    path.write_text(html, encoding="utf-8")
    export_calendar_json()

    sync_logs: list[str] = []
    try:
        import asyncio

        from workout_sync.sync import full_resync

        result = asyncio.run(full_resync(upcoming_only=True))
        sync_logs.append(
            f"COROS: removed {result.get('removed')} · pushed {result.get('pushed')}"
        )
    except Exception as e:
        sync_logs.append(f"COROS sync failed: {e}")

    try:
        from workout_sync.google_calendar import sync_google_calendar

        g = sync_google_calendar()
        sync_logs.append(
            f"GCal: created {g.created} · updated {g.updated} · deleted {g.deleted}"
        )
    except Exception as e:
        sync_logs.append(f"GCal sync skipped/failed: {e}")

    return {"changed": changed, "logs": sync_logs}
