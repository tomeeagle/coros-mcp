"""Weekly performance analysis: volume, HR, and training-load trends."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from statistics import mean
from typing import Any

from models import ActivitySummary, DailyRecord, SleepRecord
from workout_sync.weekly_coach import (
    _activity_day,
    _is_bike,
    _is_run,
    _is_strength,
    _ymd,
    monday_of,
)


@dataclass
class SportBucket:
    name: str
    count: int = 0
    distance_km: float = 0.0
    duration_min: float = 0.0
    training_load: float = 0.0
    avg_hrs: list[int] = field(default_factory=list)

    def add(self, a: ActivitySummary) -> None:
        self.count += 1
        self.distance_km += (a.distance_meters or 0) / 1000
        self.duration_min += (a.duration_seconds or 0) / 60
        self.training_load += float(a.training_load or 0)
        if a.avg_hr:
            self.avg_hrs.append(a.avg_hr)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "count": self.count,
            "distance_km": round(self.distance_km, 1),
            "duration_min": round(self.duration_min),
            "training_load": round(self.training_load),
            "avg_hr": round(mean(self.avg_hrs)) if self.avg_hrs else None,
        }


@dataclass
class WeekSnapshot:
    week_start: date
    week_end: date
    sports: dict[str, SportBucket]
    activity_count: int
    total_distance_km: float
    total_duration_min: float
    activity_training_load: float
    daily_training_load: float
    load_ratio: float | None
    avg_rhr: float | None
    avg_hrv: float | None
    avg_run_hr: float | None
    vo2max: int | None
    stamina_level: float | None
    activities: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "week_start": self.week_start.isoformat(),
            "week_end": self.week_end.isoformat(),
            "sports": {k: v.to_dict() for k, v in self.sports.items() if v.count},
            "activity_count": self.activity_count,
            "total_distance_km": round(self.total_distance_km, 1),
            "total_duration_min": round(self.total_duration_min),
            "activity_training_load": round(self.activity_training_load),
            "daily_training_load": round(self.daily_training_load),
            "load_ratio": round(self.load_ratio, 2) if self.load_ratio is not None else None,
            "avg_rhr": round(self.avg_rhr, 1) if self.avg_rhr is not None else None,
            "avg_hrv": round(self.avg_hrv, 1) if self.avg_hrv is not None else None,
            "avg_run_hr": round(self.avg_run_hr) if self.avg_run_hr is not None else None,
            "vo2max": self.vo2max,
            "stamina_level": self.stamina_level,
            "activities": self.activities,
        }


@dataclass
class TrendPoint:
    metric: str
    previous: float | None
    current: float | None
    delta: float | None
    direction: str  # up | down | flat | unknown
    note: str


@dataclass
class PerformanceReport:
    generated_at: str
    focus_week: WeekSnapshot
    prior_weeks: list[WeekSnapshot]
    trends: list[TrendPoint]
    headline: str
    notes: list[str]
    data_gaps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "headline": self.headline,
            "notes": self.notes,
            "data_gaps": self.data_gaps,
            "focus_week": self.focus_week.to_dict(),
            "prior_weeks": [w.to_dict() for w in self.prior_weeks],
            "trends": [
                {
                    "metric": t.metric,
                    "previous": t.previous,
                    "current": t.current,
                    "delta": t.delta,
                    "direction": t.direction,
                    "note": t.note,
                }
                for t in self.trends
            ],
        }


def previous_week_bounds(today: date | None = None) -> tuple[date, date]:
    """Return Mon–Sun for the most recently completed calendar week."""
    today = today or datetime.now(UTC).astimezone().date()
    this_monday = monday_of(today)
    start = this_monday - timedelta(days=7)
    return start, start + timedelta(days=6)


def _sport_key(a: ActivitySummary) -> str:
    if _is_run(a):
        return "run"
    if _is_bike(a):
        return "bike"
    if _is_strength(a):
        return "strength"
    name = (a.sport_name or a.name or "other").lower()
    if "walk" in name or "hik" in name:
        return "walk"
    if "swim" in name:
        return "swim"
    return "other"


def _empty_sports() -> dict[str, SportBucket]:
    return {
        "run": SportBucket("Running"),
        "bike": SportBucket("Cycling"),
        "strength": SportBucket("Strength"),
        "walk": SportBucket("Walk/Hike"),
        "swim": SportBucket("Swim"),
        "other": SportBucket("Other"),
    }


def _fmt_activity(a: ActivitySummary) -> dict[str, Any]:
    day = _activity_day(a)
    km = (a.distance_meters or 0) / 1000
    mins = (a.duration_seconds or 0) / 60
    return {
        "date": f"{day[:4]}-{day[4:6]}-{day[6:]}" if day and len(day) == 8 else day,
        "name": a.name or a.sport_name or "Activity",
        "sport": _sport_key(a),
        "sport_name": a.sport_name,
        "distance_km": round(km, 2) if km else 0,
        "duration_min": round(mins),
        "avg_hr": a.avg_hr,
        "training_load": a.training_load,
        "elevation_gain": a.elevation_gain,
    }


def build_week_snapshot(
    start: date,
    activities: list[ActivitySummary],
    daily: list[DailyRecord],
) -> WeekSnapshot:
    end = start + timedelta(days=6)
    start_s, end_s = _ymd(start), _ymd(end)
    sports = _empty_sports()
    week_acts: list[ActivitySummary] = []
    for a in activities:
        day = _activity_day(a)
        if day and start_s <= day <= end_s:
            week_acts.append(a)
            sports[_sport_key(a)].add(a)

    week_daily = [d for d in daily if start_s <= d.date <= end_s]
    rhrs = [d.rhr for d in week_daily if d.rhr]
    hrvs = [d.avg_sleep_hrv for d in week_daily if d.avg_sleep_hrv]
    loads = [d.training_load for d in week_daily if d.training_load]
    load_ratio = next(
        (
            d.training_load_ratio
            for d in sorted(week_daily, key=lambda x: x.date, reverse=True)
            if d.training_load_ratio
        ),
        None,
    )
    vo2 = next(
        (d.vo2max for d in sorted(week_daily, key=lambda x: x.date, reverse=True) if d.vo2max),
        None,
    )
    stamina = next(
        (d.stamina_level for d in sorted(week_daily, key=lambda x: x.date, reverse=True) if d.stamina_level),
        None,
    )
    run_hrs = sports["run"].avg_hrs

    return WeekSnapshot(
        week_start=start,
        week_end=end,
        sports=sports,
        activity_count=len(week_acts),
        total_distance_km=sum(s.distance_km for s in sports.values()),
        total_duration_min=sum(s.duration_min for s in sports.values()),
        activity_training_load=sum(s.training_load for s in sports.values()),
        daily_training_load=float(sum(loads)) if loads else 0.0,
        load_ratio=load_ratio,
        avg_rhr=mean(rhrs) if rhrs else None,
        avg_hrv=mean(hrvs) if hrvs else None,
        avg_run_hr=mean(run_hrs) if run_hrs else None,
        vo2max=vo2,
        stamina_level=stamina,
        activities=[_fmt_activity(a) for a in sorted(week_acts, key=lambda x: int(x.start_time or 0))],
    )


def _trend(
    metric: str,
    previous: float | None,
    current: float | None,
    *,
    higher_is_better: bool | None = None,
    unit: str = "",
    flat_eps: float = 0.05,
) -> TrendPoint:
    if previous is None or current is None:
        return TrendPoint(metric, previous, current, None, "unknown", f"{metric}: insufficient history")
    if previous == 0:
        delta = None
        direction = "up" if current > 0 else "flat"
        note = f"{metric}: {current}{unit} (no prior baseline)"
        return TrendPoint(metric, previous, current, delta, direction, note)

    rel = (current - previous) / abs(previous)
    if abs(rel) < flat_eps:
        direction = "flat"
    elif current > previous:
        direction = "up"
    else:
        direction = "down"
    delta = current - previous
    arrow = {"up": "↑", "down": "↓", "flat": "→"}[direction]
    quality = ""
    if higher_is_better is True and direction == "up":
        quality = " (positive)"
    elif (higher_is_better is True and direction == "down") or (
        higher_is_better is False and direction == "up"
    ):
        quality = " (watch)"
    elif higher_is_better is False and direction == "down":
        quality = " (positive)"
    note = f"{metric}: {previous:.1f}{unit} → {current:.1f}{unit} ({arrow} {delta:+.1f}){quality}"
    return TrendPoint(metric, round(previous, 2), round(current, 2), round(delta, 2), direction, note)


def _avg_prior(weeks: list[WeekSnapshot], attr: str) -> float | None:
    vals = []
    for w in weeks:
        v = getattr(w, attr)
        if v is not None:
            vals.append(float(v))
    return mean(vals) if vals else None


def build_performance_report(
    activities: list[ActivitySummary],
    daily: list[DailyRecord],
    *,
    today: date | None = None,
    prior_week_count: int = 3,
) -> PerformanceReport:
    """Build report for the previous completed week vs prior weeks."""
    today = today or datetime.now(UTC).astimezone().date()
    focus_start, _ = previous_week_bounds(today)
    focus = build_week_snapshot(focus_start, activities, daily)

    prior: list[WeekSnapshot] = []
    for i in range(1, prior_week_count + 1):
        start = focus_start - timedelta(days=7 * i)
        prior.append(build_week_snapshot(start, activities, daily))
    prior.reverse()  # oldest → newest before focus

    gaps: list[str] = []
    if focus.activity_count == 0:
        gaps.append("No activities found for the focus week — sync may be incomplete or no sessions logged.")
    if not any(d.date >= _ymd(focus_start) and d.date <= _ymd(focus.week_end) for d in daily):
        gaps.append("No daily metrics for the focus week (HRV / RHR / training load may be missing).")

    run_prior = [w.sports["run"].distance_km for w in prior]
    bike_prior = [w.sports["bike"].distance_km for w in prior]
    load_prior = _avg_prior(prior, "daily_training_load")
    if load_prior is None or load_prior == 0:
        load_prior = _avg_prior(prior, "activity_training_load")
    load_current = focus.daily_training_load or focus.activity_training_load

    trends = [
        _trend(
            "Run distance (km)",
            mean(run_prior) if run_prior else None,
            focus.sports["run"].distance_km,
            higher_is_better=True,
            unit="km",
            flat_eps=0.08,
        ),
        _trend(
            "Bike distance (km)",
            mean(bike_prior) if bike_prior else None,
            focus.sports["bike"].distance_km,
            higher_is_better=True,
            unit="km",
            flat_eps=0.1,
        ),
        _trend(
            "Weekly training load",
            load_prior,
            load_current,
            higher_is_better=None,
            flat_eps=0.1,
        ),
        _trend(
            "Resting HR",
            _avg_prior(prior, "avg_rhr"),
            focus.avg_rhr,
            higher_is_better=False,
            unit=" bpm",
            flat_eps=0.03,
        ),
        _trend(
            "Sleep HRV",
            _avg_prior(prior, "avg_hrv"),
            focus.avg_hrv,
            higher_is_better=True,
            unit=" ms",
            flat_eps=0.05,
        ),
        _trend(
            "Avg run HR",
            _avg_prior(prior, "avg_run_hr"),
            focus.avg_run_hr,
            higher_is_better=False,
            unit=" bpm",
            flat_eps=0.03,
        ),
    ]

    notes: list[str] = []
    run_km = focus.sports["run"].distance_km
    bike_km = focus.sports["bike"].distance_km
    notes.append(
        f"Volume: {run_km:.1f} km run, {bike_km:.1f} km bike, "
        f"{focus.sports['strength'].count} strength session(s), "
        f"{focus.activity_count} activities total."
    )
    load = focus.daily_training_load or focus.activity_training_load
    if load:
        ratio_bit = f", load ratio {focus.load_ratio:.2f}" if focus.load_ratio is not None else ""
        notes.append(f"Training load for the week: {load:.0f}{ratio_bit}.")
    if focus.load_ratio is not None:
        if focus.load_ratio > 1.5:
            notes.append("Acute:chronic load ratio is elevated (>1.5) — ease volume/intensity this week.")
        elif focus.load_ratio < 0.8:
            notes.append("Load ratio is low (<0.8) — room to rebuild volume if feeling fresh.")
        else:
            notes.append("Load ratio is in a sensible build range (≈0.8–1.3).")
    if focus.avg_rhr is not None:
        notes.append(f"Average resting HR: {focus.avg_rhr:.0f} bpm.")
    if focus.avg_hrv is not None:
        notes.append(f"Average sleep HRV: {focus.avg_hrv:.0f} ms.")
    if focus.vo2max is not None:
        notes.append(f"Latest VO2max: {focus.vo2max}.")
    if focus.stamina_level is not None:
        notes.append(f"Stamina/fitness level: {focus.stamina_level:.0f}.")

    for t in trends:
        if t.direction != "unknown":
            notes.append(t.note)

    # Headline
    if gaps and focus.activity_count == 0:
        headline = "No activity data for last week — cannot score progress yet."
    else:
        watch = sum(1 for t in trends if "watch" in t.note)
        positive = sum(1 for t in trends if "positive" in t.note)
        if focus.load_ratio and focus.load_ratio > 1.5:
            headline = "Solid volume, but load is ramping fast — recover deliberately."
        elif watch >= 2 and positive == 0:
            headline = "Recovery markers look stressed versus recent weeks."
        elif positive >= 2 and watch == 0:
            headline = "Progress looks healthy — volume and recovery trending well."
        elif run_km + bike_km < 10 and focus.activity_count <= 2:
            headline = "Light week — low total volume compared with a typical training block."
        else:
            headline = "Mixed week — some gains, a few signals to keep an eye on."

    return PerformanceReport(
        generated_at=datetime.now(UTC).isoformat(),
        focus_week=focus,
        prior_weeks=prior,
        trends=trends,
        headline=headline,
        notes=notes[:12],
        data_gaps=gaps,
    )


def render_markdown(report: PerformanceReport) -> str:
    """Render a human-readable markdown report (no secrets)."""
    fw = report.focus_week
    lines = [
        f"# Weekly performance — {fw.week_start.isoformat()} → {fw.week_end.isoformat()}",
        "",
        f"**{report.headline}**",
        "",
        "## Summary",
    ]
    for n in report.notes:
        lines.append(f"- {n}")
    if report.data_gaps:
        lines.append("")
        lines.append("## Data gaps")
        for g in report.data_gaps:
            lines.append(f"- {g}")

    lines.extend(["", "## Distance & sessions by sport", ""])
    lines.append("| Sport | Sessions | Distance | Duration | Avg HR | Load |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
    for key in ("run", "bike", "strength", "walk", "swim", "other"):
        s = fw.sports[key]
        if not s.count:
            continue
        hr = str(s.to_dict()["avg_hr"]) if s.avg_hrs else "—"
        lines.append(
            f"| {s.name} | {s.count} | {s.distance_km:.1f} km | "
            f"{s.duration_min:.0f} min | {hr} | {s.training_load:.0f} |"
        )

    lines.extend(["", "## Activities", ""])
    if not fw.activities:
        lines.append("_No activities in this week._")
    else:
        lines.append("| Date | Activity | Sport | Dist | Time | HR | Load |")
        lines.append("| --- | --- | --- | ---: | ---: | ---: | ---: |")
        for a in fw.activities:
            lines.append(
                f"| {a['date']} | {a['name']} | {a['sport']} | "
                f"{a['distance_km']:.1f} km | {a['duration_min']} min | "
                f"{a['avg_hr'] or '—'} | {a['training_load'] or '—'} |"
            )

    lines.extend(["", "## Trends vs prior weeks", ""])
    for t in report.trends:
        lines.append(f"- {t.note}")

    if report.prior_weeks:
        lines.extend(["", "## Prior weeks at a glance", ""])
        lines.append("| Week | Run km | Bike km | Load | RHR | HRV |")
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
        for w in report.prior_weeks + [fw]:
            lines.append(
                f"| {w.week_start.isoformat()} | {w.sports['run'].distance_km:.1f} | "
                f"{w.sports['bike'].distance_km:.1f} | "
                f"{(w.daily_training_load or w.activity_training_load):.0f} | "
                f"{(f'{w.avg_rhr:.0f}' if w.avg_rhr is not None else '—')} | "
                f"{(f'{w.avg_hrv:.0f}' if w.avg_hrv is not None else '—')} |"
            )

    lines.extend(["", f"_Generated {report.generated_at}_", ""])
    return "\n".join(lines)


def _week_axis_label(start: date) -> str:
    end = start + timedelta(days=6)
    if start.month == end.month:
        return f"{start.day}–{end.day} {start.strftime('%b')}"
    return f"{start.day} {start.strftime('%b')}–{end.day} {end.strftime('%b')}"


def _sleep_stats(
    sleeps: list[SleepRecord], start: date, end: date
) -> tuple[int, float | None, float | None, float | None]:
    hours: list[float] = []
    awake: list[float] = []
    naps: list[float] = []
    start_s, end_s = _ymd(start), _ymd(end)
    for s in sleeps:
        if not (start_s <= s.date <= end_s):
            continue
        dur = s.total_duration_minutes or 0
        if dur < 30:
            continue
        hours.append(dur / 60)
        if s.phases and s.phases.awake_minutes:
            awake.append(s.phases.awake_minutes / 60)
        if s.phases and s.phases.nap_minutes:
            naps.append(s.phases.nap_minutes / 60)
    return (
        len(hours),
        mean(hours) if hours else None,
        mean(awake) if awake else None,
        mean(naps) if naps else None,
    )


def _week_trend_point(
    snap: WeekSnapshot, sleeps: list[SleepRecord]
) -> dict[str, Any]:
    nights, sleep_h, awake_h, nap_h = _sleep_stats(sleeps, snap.week_start, snap.week_end)
    load = snap.daily_training_load or snap.activity_training_load
    gap = snap.activity_count == 0 and nights == 0 and load == 0
    return {
        "weekStart": snap.week_start.isoformat(),
        "weekEnd": snap.week_end.isoformat(),
        "label": _week_axis_label(snap.week_start),
        "runKm": round(snap.sports["run"].distance_km, 1),
        "bikeKm": round(snap.sports["bike"].distance_km, 1),
        "strengthCount": snap.sports["strength"].count,
        "load": round(load),
        "loadRatio": round(snap.load_ratio, 2) if snap.load_ratio is not None else None,
        "avgRhr": round(snap.avg_rhr, 1) if snap.avg_rhr is not None else None,
        "avgHrv": round(snap.avg_hrv, 1) if snap.avg_hrv is not None else None,
        "sleepNights": nights,
        "avgSleepHours": round(sleep_h, 1) if sleep_h is not None else None,
        "avgAwakeHours": round(awake_h, 1) if awake_h is not None else None,
        "avgNapHours": round(nap_h, 1) if nap_h is not None else None,
        "vo2max": snap.vo2max,
        "gap": gap,
    }


def _focus_daily_series(
    start: date,
    daily: list[DailyRecord],
    sleeps: list[SleepRecord],
) -> list[dict[str, Any]]:
    by_day = {d.date: d for d in daily}
    by_sleep = {s.date: s for s in sleeps}
    points = []
    for i in range(7):
        d = start + timedelta(days=i)
        ymd = _ymd(d)
        rec = by_day.get(ymd)
        sl = by_sleep.get(ymd)
        sleep_h = None
        awake_h = None
        if sl and (sl.total_duration_minutes or 0) >= 30:
            sleep_h = round((sl.total_duration_minutes or 0) / 60, 1)
            if sl.phases and sl.phases.awake_minutes:
                awake_h = round(sl.phases.awake_minutes / 60, 1)
        points.append(
            {
                "date": d.isoformat(),
                "label": d.strftime("%a"),
                "load": rec.training_load if rec and rec.training_load else 0,
                "rhr": rec.rhr if rec else None,
                "hrv": rec.avg_sleep_hrv if rec else None,
                "sleepHours": sleep_h,
                "awakeHours": awake_h,
            }
        )
    return points


def build_fatigue_read(
    weeks: list[dict[str, Any]],
    daily: list[dict[str, Any]],
) -> dict[str, Any]:
    """Plain-English read on why this week may feel exhausting."""
    if not weeks:
        return {
            "headline": "Not enough history to judge fatigue yet.",
            "summary": "Need a few weeks of Coros data first.",
            "factors": [],
        }

    focus = weeks[-1]
    prior = [w for w in weeks[:-1] if not w.get("gap")]
    factors: list[dict[str, str]] = []

    prior_sleep = [w["avgSleepHours"] for w in prior if w.get("avgSleepHours") is not None]
    prior_awake = [w["avgAwakeHours"] for w in prior if w.get("avgAwakeHours") is not None]
    prior_nap = [w["avgNapHours"] for w in prior if w.get("avgNapHours") is not None]
    prior_rhr = [w["avgRhr"] for w in prior if w.get("avgRhr") is not None]
    prior_load = [w["load"] for w in prior if w.get("load")]

    sleep_h = focus.get("avgSleepHours")
    awake_h = focus.get("avgAwakeHours")
    if sleep_h is not None and prior_sleep and sleep_h <= mean(prior_sleep) - 0.6:
        factors.append(
            {
                "title": "Nights got shorter",
                "detail": (
                    f"This week averaged {sleep_h:.1f} h of sleep vs "
                    f"~{mean(prior_sleep):.1f} h recently."
                ),
                "weight": "high",
            }
        )
    if awake_h is not None and (
        awake_h >= 0.9 or (prior_awake and awake_h >= mean(prior_awake) + 0.4)
    ):
        factors.append(
            {
                "title": "Sleep was fragmented",
                "detail": (
                    f"About {awake_h:.1f} h awake per night this week"
                    + (
                        f" vs ~{mean(prior_awake):.1f} h recently."
                        if prior_awake
                        else "."
                    )
                ),
                "weight": "high",
            }
        )

    if prior_nap and mean(prior_nap) >= 1.0:
        factors.append(
            {
                "title": "Naps have been covering a sleep debt for months",
                "detail": (
                    f"Recent weeks average ~{mean(prior_nap):.1f} h of daytime naps. "
                    "That's paying back nights, not extra recovery on top of good sleep."
                ),
                "weight": "medium",
            }
        )

    if len(weeks) >= 2 and weeks[-2].get("gap") and (focus.get("load") or 0) >= 120:
        factors.append(
            {
                "title": "Sharp return after a blank week",
                "detail": (
                    f"The week before logged no training or sleep, then this week hit "
                    f"load {focus.get('load')}. Coming back that fast feels harder than "
                    "the same load in a steady block."
                ),
                "weight": "high",
            }
        )

    if daily:
        weekend_load = sum(p.get("load") or 0 for p in daily[-3:])  # Fri–Sun
        week_load = sum(p.get("load") or 0 for p in daily)
        if week_load >= 80 and weekend_load >= week_load * 0.7:
            factors.append(
                {
                    "title": "The week was back-loaded",
                    "detail": (
                        f"{weekend_load:.0f} of {week_load:.0f} training load landed Fri–Sun. "
                        "Two long days after rest feel like a smash, even if weekly volume is modest."
                    ),
                    "weight": "high",
                }
            )
        rhrs = [p["rhr"] for p in daily if p.get("rhr") is not None]
        if rhrs and prior_rhr and max(rhrs) >= mean(prior_rhr) + 8:
            factors.append(
                {
                    "title": "Resting HR spiked",
                    "detail": (
                        f"A morning RHR of {max(rhrs):.0f} vs a recent average around "
                        f"{mean(prior_rhr):.0f}."
                    ),
                    "weight": "medium",
                }
            )

    if prior_rhr and focus.get("avgRhr") is not None:
        best = min(prior_rhr)
        if focus["avgRhr"] >= best + 5 and best <= 52:
            factors.append(
                {
                    "title": "Resting HR has drifted up since you were fresher",
                    "detail": (
                        f"Weekly average is {focus['avgRhr']:.0f} bpm; it was down around "
                        f"{best:.0f} earlier in this block."
                    ),
                    "weight": "medium",
                }
            )

    ratio = focus.get("loadRatio")
    if ratio is not None and ratio < 0.8:
        factors.append(
            {
                "title": "This is not an overtraining week",
                "detail": (
                    f"Load ratio {ratio:.2f} is below the 0.8–1.3 build band. "
                    "The drain is recovery (sleep, heat, a stacked weekend), not too much training."
                ),
                "weight": "low",
            }
        )
    elif ratio is not None and ratio > 1.5:
        factors.append(
            {
                "title": "Load is ramping faster than your base",
                "detail": f"Load ratio {ratio:.2f} is in the injury-risk zone (>1.5).",
                "weight": "high",
            }
        )

    if prior_load and (focus.get("load") or 0) > 0:
        avg_load = mean(prior_load)
        if focus["load"] <= avg_load * 0.85:
            pass  # already covered by ratio; don't double-say "light week"

    high = sum(1 for f in factors if f["weight"] == "high")
    if any("blank week" in f["title"] for f in factors) and any(
        "Sleep" in f["title"] or "Nights" in f["title"] or "fragmented" in f["title"]
        for f in factors
    ):
        headline = "Not overtrained — under-slept, then a sharp weekend after a layoff."
    elif high >= 2 and any(
        "Sleep" in f["title"] or "Nights" in f["title"] or "fragmented" in f["title"]
        for f in factors
    ):
        headline = "Sleep is the main reason this week feels heavy."
    elif ratio is not None and ratio > 1.5:
        headline = "Load is ramping fast — recover on purpose this week."
    elif factors:
        headline = "Fatigue looks like recovery debt, not a huge training block."
    else:
        headline = "No strong fatigue flags in the numbers we have."

    bits = [f["title"].rstrip(".") for f in factors[:3]]
    summary = ("; ".join(bits) + ".") if bits else "Nothing dramatic in the weekly averages."

    weight_rank = {"high": 0, "medium": 1, "low": 2}
    factors.sort(key=lambda f: weight_rank.get(f["weight"], 1))
    ratio_notes = [
        f
        for f in factors
        if "overtraining" in f["title"].lower() or "ramping faster" in f["title"].lower()
    ]
    core = [f for f in factors if f not in ratio_notes][:5]
    return {"headline": headline, "summary": summary, "factors": core + ratio_notes}


def build_coach_trends(
    activities: list[ActivitySummary],
    daily: list[DailyRecord],
    sleeps: list[SleepRecord],
    *,
    week: str | None = None,
    week_count: int = 12,
) -> dict[str, Any]:
    """Last N Mon–Sun weeks ending at the reviewed week, plus a fatigue read."""
    from workout_sync.weekly_coach import week_bounds

    focus_start, _ = week_bounds(week)
    points = []
    for i in range(week_count - 1, -1, -1):
        start = focus_start - timedelta(days=7 * i)
        snap = build_week_snapshot(start, activities, daily)
        points.append(_week_trend_point(snap, sleeps))

    daily_series = _focus_daily_series(focus_start, daily, sleeps)
    fatigue = build_fatigue_read(points, daily_series)
    return {
        "weekStart": focus_start.isoformat(),
        "weekEnd": (focus_start + timedelta(days=6)).isoformat(),
        "weeks": points,
        "daily": daily_series,
        "fatigue": fatigue,
    }


async def collect_and_build_report(
    *,
    today: date | None = None,
    prior_week_count: int = 3,
    refresh: bool = True,
) -> PerformanceReport:
    """Fetch/cache Coros data then build the performance report."""
    from cache.store import get_activities, get_daily_records, init_db
    from cache.sync import fetch_activities_cached, fetch_daily_records_cached
    from coros_api import get_stored_auth, try_auto_login

    today = today or datetime.now(UTC).astimezone().date()
    focus_start, _ = previous_week_bounds(today)
    range_start = focus_start - timedelta(days=7 * prior_week_count)
    range_end = focus_start + timedelta(days=6)
    start_s, end_s = _ymd(range_start), _ymd(range_end)

    init_db()
    auth = get_stored_auth()
    if auth is None:
        auth = await try_auto_login()

    if refresh and auth is not None:
        await fetch_daily_records_cached(auth, start_s, end_s)
        await fetch_activities_cached(auth, start_s, end_s, size=100)

    activities = get_activities(start_s, end_s)
    daily = get_daily_records(start_s, end_s)
    report = build_performance_report(
        activities,
        daily,
        today=today,
        prior_week_count=prior_week_count,
    )
    if auth is None:
        report.data_gaps.insert(
            0,
            "Not authenticated — used local cache only. "
            "Set COROS_EMAIL/COROS_PASSWORD (or COROS_ACCESS_TOKEN) to refresh from Coros.",
        )
        if report.focus_week.activity_count == 0:
            report.headline = "Cannot analyze last week: Coros auth is missing and the cache is empty."
    return report
