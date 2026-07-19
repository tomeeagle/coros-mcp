"""Tests for weekly coach review builder."""

from datetime import UTC, date, datetime
from unittest.mock import patch

from models import ActivitySummary, DailyRecord
from workout_sync.weekly_coach import build_week_review, monday_of, week_bounds


def test_week_bounds_monday():
    start, end = week_bounds("20260719")  # Sunday
    assert start == date(2026, 7, 13)
    assert end == date(2026, 7, 19)
    assert monday_of(date(2026, 7, 19)) == date(2026, 7, 13)


def test_build_week_review_shape():
    tue = datetime(2026, 7, 14, 10, 0, tzinfo=UTC)
    fake_acts = [
        ActivitySummary(
            activity_id="1",
            name="Easy 5K",
            sport_type=100,
            sport_name="Running",
            start_time=str(int(tue.timestamp())),
            duration_seconds=1800,
            distance_meters=5000,
            avg_hr=140,
        )
    ]

    with (
        patch("workout_sync.weekly_coach.get_activities", return_value=fake_acts),
        patch("workout_sync.weekly_coach.get_daily_records", return_value=[]),
        patch("workout_sync.weekly_coach.init_db"),
    ):
        review = build_week_review("20260714")

    payload = review.to_dict()
    assert payload["weekStart"] == "2026-07-13"
    assert len(payload["days"]) == 7
    assert payload["headline"]
    assert isinstance(payload["notes"], list)
    assert "weekLoad" in payload["stats"]
    assert "doneRunKm" in payload["stats"]
    assert "bikeKm" in payload["stats"]
    tue_day = next(d for d in payload["days"] if d["date"] == "2026-07-14")
    assert tue_day["activities"]
    assert tue_day["activities"][0]["kind"] == "run"


def test_hard_run_on_easy_day_is_flagged():
    tue = datetime(2026, 7, 14, 10, 0, tzinfo=UTC)
    acts = [
        ActivitySummary(
            activity_id="1",
            name="Tempo blowup",
            sport_type=100,
            sport_name="Running",
            start_time=str(int(tue.timestamp())),
            duration_seconds=2400,
            distance_meters=8000,
            avg_hr=168,
            elevation_gain=20,
        )
    ]
    daily = [DailyRecord(date="20260710", lthr=162, rhr=48)]

    def fake_get_activities(s, e, **_):
        return acts if s <= "20260714" <= e else []

    with (
        patch("workout_sync.weekly_coach.get_activities", side_effect=fake_get_activities),
        patch("workout_sync.weekly_coach.get_daily_records", return_value=daily),
        patch("workout_sync.weekly_coach.init_db"),
    ):
        review = build_week_review("20260714")

    tue_day = next(d for d in review.to_dict()["days"] if d["date"] == "2026-07-14")
    act = tue_day["activities"][0]
    assert act["hard"] is True
    assert "threshold" in act["reason"].lower()


def test_easy_run_not_flagged():
    tue = datetime(2026, 7, 14, 10, 0, tzinfo=UTC)
    acts = [
        ActivitySummary(
            activity_id="1",
            name="Easy jog",
            sport_type=100,
            sport_name="Running",
            start_time=str(int(tue.timestamp())),
            duration_seconds=2100,
            distance_meters=5000,
            avg_hr=128,
        )
    ]
    daily = [DailyRecord(date="20260710", lthr=162, rhr=48)]

    def fake_get_activities(s, e, **_):
        return acts if s <= "20260714" <= e else []

    with (
        patch("workout_sync.weekly_coach.get_activities", side_effect=fake_get_activities),
        patch("workout_sync.weekly_coach.get_daily_records", return_value=daily),
        patch("workout_sync.weekly_coach.init_db"),
    ):
        review = build_week_review("20260714")

    tue_day = next(d for d in review.to_dict()["days"] if d["date"] == "2026-07-14")
    assert tue_day["activities"][0]["hard"] is False
