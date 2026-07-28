"""Tests for training plan HTML parsing."""

from datetime import date

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


@pytest.mark.skipif(not PLAN.is_file(), reason="training_plan.html not in repo")
def test_parse_week_dates_cross_month():
    assert _parse_week_dates("29 Jun – 6 Jul") == ((6, 29), (7, 6))
    assert _parse_week_dates("27 Jul – 2 Aug") == ((7, 27), (8, 2))


def test_parse_week_dates_single_month():
    assert _parse_week_dates("8–14 Jun") == ((6, 8), (6, 14))
    assert _parse_week_dates("18–21 Jun") == ((6, 18), (6, 21))
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
        "Easy 3K (separate from strength)",
        "💪 Strength WK1",
        "20260608",
        {"20260608": "wk1"},
    )
    assert skip is None
    assert keys == ["strength_wk1", "easy_3k"]


def test_monday_strength_only_when_no_post_run():
    keys, skip = _map_run_to_workouts(
        "Dumbbell strength — 45 mins max",
        "💪 Strength WK4 — strength only",
        "20260706",
        {},
    )
    assert skip is None
    assert keys == ["strength_wk4"]


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


def test_map_build_8k():
    assert _map_run_to_workout(
        "Build 8K — 5K easy / 1K moderate / 1K hard / 1K push",
        "",
        "20260618",
        {},
    ) == ("build_8k", None)


@pytest.mark.skipif(not PLAN.is_file(), reason="training_plan.html not in repo")
def test_parse_full_plan():
    plan = parse_plan_html(PLAN)
    assert plan.year == 2026
    assert len(plan.weeks) == 8

    # Re-entry week — pivoted to fire service bleep after baseline 6.2
    assert plan.schedule["20260719"] == ["easy_3k"]
    assert "20260720" not in plan.schedule
    assert plan.schedule["20260723"] == ["bleep_practice"]
    assert plan.schedule["20260725"] == ["easy_4k_shuttle"]  # rough — no full MSFT
    assert plan.schedule["20260727"] == ["shuttle_pace"]
    assert plan.schedule["20260728"] == ["easy_5k"]
    assert plan.schedule["20260729"] == ["bleep_practice"]
    assert plan.schedule["20260730"] == ["easy_5k"]
    assert plan.schedule["20260731"] == ["easy_5k"]
    assert "20260801" not in plan.schedule  # Gower optional — not prescribed
    assert "20260802" not in plan.schedule
    assert plan.schedule["20260803"] == ["easy_5k"]
    assert plan.schedule["20260804"] == ["shuttle_pace"]
    assert "20260805" not in plan.schedule  # taper rest
    assert "20260806" not in plan.schedule
    assert "20260807" not in plan.schedule
    assert plan.schedule["20260808"] == ["bleep_test"]

    # Tue 21 skipped (rest); Wed still easy default
    assert "20260721" not in plan.schedule
    assert plan.schedule["20260722"] == ["easy_5k"]
    # Later BAC/PFTC weeks still use easy default when optional
    assert plan.schedule["20260811"] == ["easy_6k"]

    # Peak and deload
    assert plan.schedule["20260905"] == ["long_14k"]
    assert plan.schedule["20260912"] == ["long_10k"]


@pytest.mark.skipif(not PLAN.is_file(), reason="training_plan.html not in repo")
def test_strength_thursdays_from_html():
    html = PLAN.read_text(encoding="utf-8")
    days = _parse_strength_mondays(html, 2026)
    # Bleep block: no strength 24 Jul–8 Aug. WK2 slides to Thu 27 Aug.
    assert "20260730" not in days
    assert days["20260813"] == "wk4"
    assert days["20260827"] == "wk2"
    assert days["20260910"] == "wk5"
