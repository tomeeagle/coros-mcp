"""Tests for timed strength circuit presets."""

from workout_sync.strength import ROUND_REST_SECONDS, build_strength_exercises


def test_wk1_circuit_is_time_based():
    exercises = build_strength_exercises("wk1")
    assert len(exercises) == 7
    assert all(ex["target_type"] == 2 for ex in exercises)
    assert all(ex["sets"] == 1 for ex in exercises)
    assert exercises[0]["target_value"] == 40  # goblet work
    assert exercises[3]["target_value"] == 80  # row: sided L+R
    assert exercises[-1]["target_value"] == 45  # farmers carry
    assert exercises[-1]["rest_seconds"] == ROUND_REST_SECONDS


def test_wk3_has_four_circuit_rounds_in_workout_key():
    from workout_sync.workouts import WORKOUTS

    assert WORKOUTS["strength_wk3"]["circuit_sets"] == 4
