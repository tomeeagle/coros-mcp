"""Tests for training plan HTML parsing."""

from datetime import date
from pathlib import Path

import pytest

from workout_sync.plan_html import (
    DEFAULT_PLAN_PATH,
    _map_run_to_workout,
    _parse_day_label,
    _parse_strength_mondays,
    _parse_week_dates,
    parse_plan_html,
)

PLAN = DEFAULT_PLAN_PATH


@pytest.mark.skipif(not PLAN.is_file(), reason="plan_v1_8.html not in repo")
def test_parse_week_dates_cross_month():
    assert _parse_week_dates("29 Jun – 6 Jul") == ((6, 29), (7, 6))


def test_parse_week_dates_single_month():
    assert _parse_week_dates("8–14 Jun") == ((6, 8), (6, 14))


def test_parse_day_label_explicit_month():
    d = _parse_day_label("Wed 1 Jul", (6, 29), (7, 6), 2026)
    assert d == date(2026, 7, 1)


def test_parse_day_label_inferred_month():
    d = _parse_day_label("Tue 9", (6, 8), (6, 14), 2026)
    assert d == date(2026, 6, 9)


def test_map_run_club_and_race():
    assert _map_run_to_workout("Run club 8K easy", "", "20260610", {}) == ("run_club_8k", None)
    assert _map_run_to_workout("Run club — easy option only, 5K max", "", "x", {}) == (
        "run_club_5k",
        None,
    )
    assert _map_run_to_workout("RACE DAY — run it properly", "", "x", {}) == ("race_open", None)
    assert _map_run_to_workout(
        "7:30pm start — fell race",
        "🏔️ CALVER PEAK FELL RACE",
        "x",
        {},
    ) == ("race_calver", None)


@pytest.mark.skipif(not PLAN.is_file(), reason="plan_v1_8.html not in repo")
def test_parse_full_plan():
    plan = parse_plan_html(PLAN)
    assert plan.year == 2026
    assert len(plan.weeks) >= 6
    assert plan.schedule["20260609"] == "tempo_7k"
    assert plan.schedule["20260613"] == "long_14k"
    assert plan.schedule["20260616"] == "tempo_8k"
    assert plan.schedule["20260601"] == "strength_wk1"
    assert plan.schedule["20260608"] == "strength_wk2"
    assert plan.schedule["20260530"] == "race_maverick"
    assert plan.schedule["20260603"] == "race_calver"
    assert plan.schedule["20260606"] == "race_alport_16k"
    assert plan.schedule["20260610"] == "run_club_8k"
    assert plan.schedule["20260628"] == "race_bakewell"
    assert plan.schedule["20260704"] == "race_love_trails"
    # Rest days still skipped
    assert "20260531" not in plan.schedule


@pytest.mark.skipif(not PLAN.is_file(), reason="plan_v1_8.html not in repo")
def test_strength_mondays_from_html():
    html = PLAN.read_text(encoding="utf-8")
    mondays = _parse_strength_mondays(html, 2026)
    assert mondays["20260601"] == "wk1"
    assert mondays["20260629"] == "wk5"
