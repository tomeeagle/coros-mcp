"""Tests for training plan HTML parsing."""

from datetime import date
from pathlib import Path

import pytest

from workout_sync.plan_html import (
    DEFAULT_PLAN_PATH,
    _map_run_to_workout,
    _map_run_to_workouts,
    _parse_day_label,
    _parse_strength_mondays,
    _parse_week_dates,
    parse_plan_html,
)

PLAN = DEFAULT_PLAN_PATH


@pytest.mark.skipif(not PLAN.is_file(), reason="plan_v1_8.html not in repo")
def test_parse_week_dates_cross_month():
    assert _parse_week_dates("29 Jun – 6 Jul") == ((6, 29), (7, 6))
    assert _parse_week_dates("27 Jul – 2 Aug") == ((7, 27), (8, 2))


def test_parse_week_dates_single_month():
    assert _parse_week_dates("8–14 Jun") == ((6, 8), (6, 14))
    assert _parse_week_dates("3–9 Aug") == ((8, 3), (8, 9))


def test_parse_week_dates_single_day():
    assert _parse_week_dates("6 Jul") == ((7, 6), (7, 6))


def test_parse_day_label_explicit_month():
    d = _parse_day_label("Wed 1 Jul", (6, 29), (7, 6), 2026)
    assert d == date(2026, 7, 1)


def test_parse_day_label_inferred_month():
    d = _parse_day_label("Tue 9", (6, 8), (6, 14), 2026)
    assert d == date(2026, 6, 9)


def test_map_rest_to_streak_and_one_run_per_day():
    assert _map_run_to_workout("Rest", "", "x", {}) == (None, "empty")
    keys, skip = _map_run_to_workouts(
        "7K tempo — 10min easy / 20min tempo / 10min easy",
        "Tempo AM · BAC 6pm intervals",
        "20260602",
        {},
    )
    assert skip is None
    assert keys == ["bac_intervals"]


def test_monday_strength_includes_streak_3k():
    keys, skip = _map_run_to_workouts(
        "Dumbbell strength — 45 mins max",
        "💪 Strength WK1 + easy 3K after",
        "20260601",
        {"20260601": "wk1"},
    )
    assert skip is None
    assert keys == ["strength_wk1", "easy_3k"]


def test_monday_strength_only_when_no_post_run():
    keys, skip = _map_run_to_workouts(
        "Dumbbell strength — 45 mins max",
        "💪 Strength WK1 — no run after",
        "20260615",
        {},
    )
    assert skip is None
    assert keys == ["strength_wk1"]


def test_strength_preset_from_note_overrides_date():
    keys, _ = _map_run_to_workouts(
        "Dumbbell strength — 45 mins max",
        "💪 Strength WK3 — strength only",
        "20260727",
        {"20260727": "wk1"},
    )
    assert keys == ["strength_wk3"]


def test_map_run_club_and_race():
    assert _map_run_to_workout("Run club 8K easy", "", "20260610", {}) == ("run_club_8k", None)
    assert _map_run_to_workout("Run club — easy option only, 5K max", "", "x", {}) == (
        "run_club_5k",
        None,
    )
    assert _map_run_to_workout("RACE DAY — run it properly", "", "x", {}) == ("race_open", None)
    assert _map_run_to_workout(
        "Bakewell pudding race — 10.4K fell (or easy 5K streak if not racing)",
        "Optional Bakewell Pudding 10.4K 11am",
        "20260628",
        {},
    ) == ("race_bakewell", None)


@pytest.mark.skipif(not PLAN.is_file(), reason="plan_v1_8.html not in repo")
def test_parse_full_plan():
    plan = parse_plan_html(PLAN)
    assert plan.year == 2026
    assert len(plan.weeks) == 9  # finish-out + weeks 1–8

    # Finish out (8–14 Jun)
    assert plan.schedule["20260612"] == ["progression_8k"]
    assert plan.schedule["20260613"] == ["long_12k"]
    assert "20260614" not in plan.schedule

    # Week 1 (15–21 Jun) — 4 runs, strength WK1
    assert plan.schedule["20260615"] == ["strength_wk1"]
    assert plan.schedule["20260616"] == ["bac_threshold_4x6"]
    assert plan.schedule["20260617"] == ["run_club_8k"]
    assert "20260618" not in plan.schedule
    assert plan.schedule["20260619"] == ["progression_10k"]
    assert plan.schedule["20260620"] == ["long_14k"]

    # Week 2
    assert plan.schedule["20260622"] == ["strength_wk2"]
    assert plan.schedule["20260623"] == ["tempo_6k"]
    assert plan.schedule["20260626"] == ["progression_8k"]
    assert plan.schedule["20260627"] == ["long_12k"]

    # Week 3 — Love Trails
    assert plan.schedule["20260629"] == ["strength_wk5"]
    assert plan.schedule["20260630"] == ["easy_4k"]
    assert plan.schedule["20260704"] == ["race_love_trails"]

    # Week 4 — recovery
    assert plan.schedule["20260706"] == ["strength_wk4"]
    assert plan.schedule["20260707"] == ["easy_5k"]
    assert plan.schedule["20260711"] == ["long_10k"]

    # Week 5
    assert plan.schedule["20260713"] == ["strength_wk1"]
    assert plan.schedule["20260714"] == ["bac_intervals"]

    # Week 8 — block end
    assert plan.schedule["20260804"] == ["bac_threshold_4x6"]
    assert plan.schedule["20260807"] == ["easy_10k"]
    assert "20260809" not in plan.schedule

    # Old block dates removed
    assert "20260601" not in plan.schedule
    assert "20260530" not in plan.schedule


@pytest.mark.skipif(not PLAN.is_file(), reason="plan_v1_8.html not in repo")
def test_strength_mondays_from_html():
    html = PLAN.read_text(encoding="utf-8")
    mondays = _parse_strength_mondays(html, 2026)
    assert mondays["20260615"] == "wk1"
    assert mondays["20260629"] == "wk5"
    assert mondays["20260713"] == "wk3"
