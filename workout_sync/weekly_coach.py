"""Rule-based weekly coach: Coros activities vs training_plan.html."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import Any

from cache.store import get_activities, get_daily_records, init_db
from models import ActivitySummary
from workout_sync.plan_html import parse_plan_html
from workout_sync.workouts import WORKOUTS

# Sport types treated as running for volume / HR comparisons
_RUN_SPORTS = {1, 100, 101, 102, 103}
_BIKE_SPORTS = {200, 201, 202, 204}
_STRENGTH_SPORTS = {8, 9, 18}
_HARD_KEYS = ("bac_", "progression_", "tempo_", "build_", "race_")


@dataclass
class DayActivity:
    kind: str  # run | bike | strength | other
    label: str
    hard: bool = False
    reason: str | None = None


@dataclass
class DayReview:
    date: str
    planned: str | None
    done: str | None
    status: str  # matched | missed | extra | rest | upcoming | pending
    planned_kind: str | None = None
    activities: list[DayActivity] = field(default_factory=list)


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
            "days": [
                {
                    "date": d.date,
                    "planned": d.planned,
                    "plannedKind": d.planned_kind,
                    "done": d.done,
                    "status": d.status,
                    "activities": [
                        {
                            "kind": a.kind,
                            "label": a.label,
                            "hard": a.hard,
                            "reason": a.reason,
                        }
                        for a in d.activities
                    ],
                }
                for d in self.days
            ],
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


def _is_bike(a: ActivitySummary) -> bool:
    if a.sport_type in _BIKE_SPORTS:
        return True
    sport = (a.sport_name or "").lower()
    return "mtb" in sport or "bike" in sport or "cycl" in sport


def _is_strength(a: ActivitySummary) -> bool:
    if a.sport_type in _STRENGTH_SPORTS:
        return True
    sport = (a.sport_name or a.name or "").lower()
    return "strength" in sport or "weight" in sport or "gym" in sport


def _activity_kind(a: ActivitySummary) -> str:
    if _is_run(a):
        return "run"
    if _is_bike(a):
        return "bike"
    if _is_strength(a):
        return "strength"
    return "other"


def _planned_kind(keys: list[str]) -> str | None:
    if not keys:
        return None
    if any(k.startswith("strength_") for k in keys):
        return "strength"
    if any(k.startswith(("easy_", "long_", "bac_", "run_club_", "progression_", "tempo_", "build_")) for k in keys):
        return "run"
    return "other"


def _format_activity(a: ActivitySummary) -> str:
    km = (a.distance_meters or 0) / 1000
    mins = (a.duration_seconds or 0) / 60
    bit = a.name or a.sport_name or "Activity"
    if km >= 0.3:
        bit += f" · {km:.1f}km"
    elif mins >= 1:
        bit += f" · {mins:.0f}min"
    if _is_run(a) and km >= 1 and mins >= 1:
        pace_s = (a.duration_seconds or 0) / km
        bit += f" · {int(pace_s // 60)}:{int(pace_s % 60):02d}/km"
    if a.avg_hr:
        bit += f" · HR {a.avg_hr}"
    return bit


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

    today = datetime.now(UTC).astimezone().date()
    week_over = today > end
    week_ending = today >= end  # Sunday of the reviewed week, or later
    days_left = max(0, (end - max(today, start - timedelta(days=1))).days) if not week_over else 0

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

    days: list[DayReview] = []
    planned_run_km = 0.0
    done_run_km = 0.0
    bike_km = 0.0
    run_hrs: list[int] = []
    missed_hard = 0
    missed_easy = 0
    extras: list[str] = []
    high_hr_notes: list[str] = []
    hard_done = 0
    mtb_minutes = 0.0

    # Recent easy-run HR baseline (prior 28 days ending before week).
    # Needs a real sample — a couple of runs after a layoff is not a baseline.
    hist_start = _ymd(start - timedelta(days=28))
    hist_end = _ymd(start - timedelta(days=1))
    hist = [a for a in get_activities(hist_start, hist_end) if _is_run(a) and a.avg_hr]
    easy_hrs = [a.avg_hr for a in hist if a.avg_hr and (a.distance_meters or 0) < 12000]
    baseline_hr = (sum(easy_hrs) / len(easy_hrs)) if len(easy_hrs) >= 3 else None

    # Physiology context from daily records (28 days back through this week)
    hist_daily = get_daily_records(hist_start, end_s)
    lthr = next(
        (r.lthr for r in sorted(hist_daily, key=lambda r: r.date, reverse=True) if r.lthr),
        None,
    )
    hist_rhrs = [r.rhr for r in hist_daily if r.rhr and r.date < start_s]
    week_rhrs = [r.rhr for r in hist_daily if r.rhr and start_s <= r.date <= end_s]
    load_ratio = next(
        (
            r.training_load_ratio
            for r in sorted(hist_daily, key=lambda r: r.date, reverse=True)
            if r.training_load_ratio and start_s <= r.date <= end_s
        ),
        None,
    )

    for i in range(7):
        d = start + timedelta(days=i)
        ymd = _ymd(d)
        keys = _day_plan_labels(schedule, ymd)
        planned_label = _label_for_keys(keys) if keys else None
        acts = by_day.get(ymd, [])
        planned_hard_day = any(_is_hard_key(k) for k in keys)
        planned_easy_day = bool(keys) and not planned_hard_day and any(
            k.startswith(("easy_", "long_", "run_club_")) for k in keys
        )
        day_acts: list[DayActivity] = []
        done_bits = []
        for a in acts:
            km = (a.distance_meters or 0) / 1000
            label = _format_activity(a)
            kind = _activity_kind(a)
            reason = None
            if _is_run(a):
                done_run_km += km
                if a.avg_hr:
                    run_hrs.append(a.avg_hr)
                reason = _activity_flag(
                    a,
                    km,
                    planned_easy=planned_easy_day or not keys,
                    planned_hard=planned_hard_day,
                    baseline_hr=baseline_hr,
                    lthr=lthr,
                )
                note = _high_hr_note(a, d, km, baseline_hr, lthr)
                if note:
                    high_hr_notes.append(note)
            day_acts.append(
                DayActivity(kind=kind, label=label, hard=reason is not None, reason=reason)
            )
            done_bits.append(label)
            if _is_bike(a):
                bike_km += km
                mtb_minutes += (a.duration_seconds or 0) / 60

        done_label = " · ".join(done_bits) if done_bits else None
        planned_run_km += _planned_km(keys)

        if d > today and not acts:
            status = "upcoming"
        elif not keys and not acts:
            status = "rest"
        elif keys and not acts:
            if d == today:
                status = "pending"  # today isn't over — don't call it missed yet
            else:
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
                planned_kind=_planned_kind(keys),
                activities=day_acts,
            )
        )

    notes: list[str] = []
    suggestions: list[Suggestion] = []
    load_vals = [daily[k].training_load for k in daily if daily[k].training_load]
    week_load = sum(load_vals) if load_vals else 0
    future_week = start > today

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

    if load_ratio is not None:
        if load_ratio > 1.5:
            hard_flags += 1
            notes.append(
                f"Your load ratio is {load_ratio:.1f} — you're ramping up much faster than "
                "your recent base. Injury risk zone; ease back."
            )
        elif load_ratio > 1.3:
            notes.append(
                f"Load ratio {load_ratio:.1f} — building quickly. Fine for a week or two, "
                "just don't stack another big jump on top."
            )
        elif 0.8 <= load_ratio <= 1.3:
            notes.append(f"Load ratio {load_ratio:.1f} — building at a sensible rate.")

    if hist_rhrs and week_rhrs:
        rhr_base = sum(hist_rhrs) / len(hist_rhrs)
        rhr_week = sum(week_rhrs) / len(week_rhrs)
        if rhr_week >= rhr_base + 5:
            hard_flags += 1
            notes.append(
                f"Resting heart rate is up (~{rhr_week:.0f} vs ~{rhr_base:.0f} recently) — "
                "a sign you're carrying fatigue or fighting something off."
            )

    for n in high_hr_notes[:2]:
        notes.append(n)
        hard_flags += 1

    if missed_easy + missed_hard >= 2:
        notes.append(f"You missed {missed_easy + missed_hard} planned sessions.")
    elif missed_easy + missed_hard == 1:
        notes.append("One planned session was skipped.")

    if extras:
        notes.append(f"Extra sessions on {', '.join(extras)}.")

    # Headline — phrased for where we are in the week
    if future_week:
        headline = "This week hasn't happened yet."
        soften = False
        notes = [f"{planned_run_km:.0f}km of running planned. Check back once it's underway."]
    elif hard_flags >= 2 or (done_run_km >= planned_run_km * 1.35 and planned_run_km >= 10):
        headline = "You went a bit hard this week." if week_over else "You're going a bit hard so far."
        soften = True
    elif week_over and (
        missed_easy + missed_hard >= 3
        or (done_run_km < planned_run_km * 0.55 and planned_run_km >= 10)
    ):
        headline = "This week was lighter than planned."
        soften = False
    elif missed_easy + missed_hard == 0 and abs(done_run_km - planned_run_km) <= max(3, planned_run_km * 0.2):
        headline = "Nice — you stayed about on track." if week_over else "On track so far."
        soften = False
    else:
        headline = (
            "Decent week — a few things to tidy up." if week_over else "Decent week so far."
        )
        soften = hard_flags >= 1

    if not week_over and not future_week and days_left > 0:
        notes.append(
            f"{days_left} day{'s' if days_left != 1 else ''} of this week still to go — "
            "the verdict below is provisional."
        )

    if not notes:
        notes.append("No big red flags from the data we have.")

    # Next week suggestions — only once the reviewed week is done (or on its final day)
    next_start = end + timedelta(days=1)
    next_keys_by_day = {
        _ymd(next_start + timedelta(days=i)): schedule.get(_ymd(next_start + timedelta(days=i)), [])
        for i in range(7)
    }

    if not week_ending:
        soften = False  # too early to rewrite next week

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
    elif week_ending and missed_easy + missed_hard >= 2:
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
            "bikeKm": round(bike_km, 1),
            "bikeMinutes": round(mtb_minutes),
            "weekLoad": week_load,
            "loadRatio": round(load_ratio, 2) if load_ratio is not None else None,
            "avgRunHr": round(sum(run_hrs) / len(run_hrs)) if run_hrs else None,
            "avgRhr": round(sum(week_rhrs) / len(week_rhrs)) if week_rhrs else None,
            "activityCount": len(activities),
        },
    )


def _friendly_day(d: date) -> str:
    return d.strftime("%A")


def _run_effort_zone(
    hr: int, lthr: int | None, baseline_hr: float | None
) -> str | None:
    """Classify a run's average HR as tempo/threshold, or None if easy/steady."""
    if lthr:
        pct = hr / lthr
        if pct >= 1.0:
            return "threshold"
        if pct >= 0.92:
            return "tempo"
        return None
    # No LTHR on record — fall back to an easy-run baseline if we have a real one
    if baseline_hr and hr >= 140:
        if hr >= baseline_hr + 22:
            return "threshold"
        if hr >= baseline_hr + 14:
            return "tempo"
    return None


def _activity_flag(
    a: ActivitySummary,
    km: float,
    *,
    planned_easy: bool,
    planned_hard: bool,
    baseline_hr: float | None,
    lthr: int | None,
) -> str | None:
    """Explain why a single run looks harder than it should have been.

    Only flags endurance runs (>=3km) done at tempo/threshold effort when the
    day was meant to be easy (or was an unplanned extra). Planned quality
    sessions are expected to be hard, so they're never flagged.
    """
    if not _is_run(a) or planned_hard:
        return None
    hr = a.avg_hr
    if not hr or km < 3:
        return None
    zone = _run_effort_zone(hr, lthr, baseline_hr)
    if zone is None:
        return None
    gain_per_km = (a.elevation_gain or 0) / km
    hilly = gain_per_km > 25
    # On hills HR runs high naturally — only a genuine threshold effort is notable
    if hilly and zone != "threshold":
        return None

    if lthr:
        effort = (
            f"avg HR {hr} was at threshold (your LTHR is {lthr})"
            if zone == "threshold"
            else f"avg HR {hr} sat in the tempo zone (~{lthr} threshold)"
        )
    else:
        effort = f"avg HR {hr} vs ~{baseline_hr:.0f} easy baseline"

    intent = " on a day meant to be easy" if planned_easy else " on an easy/extra run"
    hills = " even allowing for the hills" if hilly else ""
    verb = "That's a hard effort" if zone == "threshold" else "Harder than easy"
    return f"{effort[0].upper()}{effort[1:]}{intent}. {verb}{hills}."


def _high_hr_note(
    a: ActivitySummary, d: date, km: float, baseline_hr: float | None, lthr: int | None
) -> str | None:
    """Flag a run's HR only when it's high by several independent measures.

    Guards against false positives: short runs, hilly/trail terrain (HR runs
    high on climbs), runs clearly below lactate threshold, and genuinely easy
    absolute HRs.
    """
    hr = a.avg_hr
    if not hr or km < 3:
        return None
    if hr < 140:  # comfortably easy in absolute terms, whatever the baseline says
        return None
    if lthr and hr < lthr * 0.88:  # well under threshold — an easy/steady effort
        return None
    gain_per_km = (a.elevation_gain or 0) / km
    if gain_per_km > 25:  # hilly/trail — elevated HR is expected
        return None
    if baseline_hr is None or hr < baseline_hr + 12:
        return None
    return (
        f"Heart rate looked high on {_friendly_day(d)}'s "
        f"{(a.name or 'run').lower()} (avg {hr} vs ~{baseline_hr:.0f} easy baseline)."
    )


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
