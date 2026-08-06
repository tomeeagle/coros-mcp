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
    assert exercises[-1]["rest_seconds"] == 0  # single lap: no rest after finisher


def test_wk4_expands_three_laps_on_sync():
    exercises = build_strength_exercises("wk4", rounds=3)
    assert len(exercises) == 21  # 7 stations × 3 laps
    assert exercises[-1]["rest_seconds"] == 0  # final station, no rest
    assert exercises[6]["rest_seconds"] == ROUND_REST_SECONDS  # end of lap 1
    assert exercises[13]["rest_seconds"] == ROUND_REST_SECONDS  # end of lap 2


def test_wk3_has_four_circuit_rounds_in_workout_key():
    from workout_sync.workouts import WORKOUTS

    assert WORKOUTS["strength_wk3"]["circuit_sets"] == 4
