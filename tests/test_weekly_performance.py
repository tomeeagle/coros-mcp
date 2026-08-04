"""Tests for weekly performance analysis."""

from datetime import UTC, date, datetime, timedelta

from models import ActivitySummary, DailyRecord
from workout_sync.weekly_performance import (
    build_performance_report,
    build_week_snapshot,
    previous_week_bounds,
    render_markdown,
)


def _ts(d: date, hour: int = 8) -> str:
    dt = datetime(d.year, d.month, d.day, hour, 0, tzinfo=UTC)
    return str(int(dt.timestamp()))


def _run(day: date, km: float, hr: int, load: int = 20) -> ActivitySummary:
    return ActivitySummary(
        activity_id=f"run-{day.isoformat()}",
        name="Easy run",
        sport_type=100,
        sport_name="Running",
        start_time=_ts(day),
        duration_seconds=int(km * 360),
        distance_meters=km * 1000,
        avg_hr=hr,
        training_load=load,
    )


def _bike(day: date, km: float, hr: int = 130) -> ActivitySummary:
    return ActivitySummary(
        activity_id=f"bike-{day.isoformat()}",
        name="Ride",
        sport_type=200,
        sport_name="Road Bike",
        start_time=_ts(day, 10),
        duration_seconds=int(km * 180),
        distance_meters=km * 1000,
        avg_hr=hr,
        training_load=15,
    )


def test_previous_week_bounds_from_tuesday():
    # Tuesday 4 Aug 2026 → previous Mon 27 Jul – Sun 2 Aug
    start, end = previous_week_bounds(date(2026, 8, 4))
    assert start == date(2026, 7, 27)
    assert end == date(2026, 8, 2)


def test_previous_week_bounds_from_monday():
    # On Monday, previous week is the week that just ended yesterday
    start, end = previous_week_bounds(date(2026, 8, 3))
    assert start == date(2026, 7, 27)
    assert end == date(2026, 8, 2)


def test_build_week_snapshot_splits_sports():
    start = date(2026, 7, 27)
    acts = [
        _run(date(2026, 7, 28), 5.0, 140),
        _bike(date(2026, 7, 29), 20.0),
        _run(date(2026, 7, 31), 10.0, 145, load=40),
    ]
    daily = [
        DailyRecord(date="20260728", rhr=50, avg_sleep_hrv=60.0, training_load=25),
        DailyRecord(date="20260729", rhr=51, avg_sleep_hrv=58.0, training_load=20, training_load_ratio=1.1),
        DailyRecord(date="20260731", rhr=52, avg_sleep_hrv=55.0, training_load=40, vo2max=52),
    ]
    snap = build_week_snapshot(start, acts, daily)
    assert snap.sports["run"].distance_km == 15.0
    assert snap.sports["bike"].distance_km == 20.0
    assert snap.activity_count == 3
    assert snap.avg_rhr == 51.0
    assert snap.vo2max == 52
    assert snap.load_ratio == 1.1


def test_build_performance_report_trends():
    today = date(2026, 8, 4)
    focus_start = date(2026, 7, 27)
    prior_start = focus_start - timedelta(days=7)

    activities = [
        _run(prior_start + timedelta(days=1), 8.0, 138, load=25),
        _run(prior_start + timedelta(days=3), 8.0, 140, load=25),
        _run(focus_start + timedelta(days=1), 12.0, 142, load=35),
        _run(focus_start + timedelta(days=3), 12.0, 144, load=35),
        _bike(focus_start + timedelta(days=2), 30.0),
    ]
    daily = []
    for i in range(14):
        d = prior_start + timedelta(days=i)
        daily.append(
            DailyRecord(
                date=d.strftime("%Y%m%d"),
                rhr=48 if i < 7 else 50,
                avg_sleep_hrv=65.0 if i < 7 else 62.0,
                training_load=30 if i < 7 else 40,
                training_load_ratio=1.05 if i == 13 else None,
            )
        )

    report = build_performance_report(activities, daily, today=today, prior_week_count=1)
    assert report.focus_week.week_start == focus_start
    assert report.focus_week.sports["run"].distance_km == 24.0
    assert report.focus_week.sports["bike"].distance_km == 30.0
    assert len(report.prior_weeks) == 1
    assert report.headline
    assert report.trends
    md = render_markdown(report)
    assert "Weekly performance" in md
    assert "Running" in md
    assert "Cycling" in md


def test_empty_week_reports_gap():
    report = build_performance_report([], [], today=date(2026, 8, 4), prior_week_count=1)
    assert report.focus_week.activity_count == 0
    assert report.data_gaps
    assert "No activity data" in report.headline or report.data_gaps
