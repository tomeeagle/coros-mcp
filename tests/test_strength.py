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


_SIDED = {
    "thoracic_rotation",
    "lunge_stretch",
    "single_leg_bridge",
    "clamshell",
    "bird_dog",
    "dead_bug",
}


def test_back_rebuild_phases_are_ten_minutes():
    from workout_sync.strength import STRENGTH_PRESETS

    for key in ("back_rebuild_1", "back_rebuild_2", "back_rebuild_3", "back_keep"):
        blocks = STRENGTH_PRESETS[key]
        total = sum(b["target_value"] + b["rest_seconds"] for b in blocks)
        assert total == 600, key
        assert blocks[-1]["rest_seconds"] == 0
        keys = [b["key"] for b in blocks]
        i = 0
        while i < len(keys):
            if keys[i] in _SIDED:
                assert i + 1 < len(keys) and keys[i + 1] == keys[i], (key, keys[i], i)
                i += 2
            else:
                i += 1
        build_strength_exercises(key)


def test_wk3_has_four_circuit_rounds_in_workout_key():
    from workout_sync.workouts import WORKOUTS

    assert WORKOUTS["strength_wk3"]["circuit_sets"] == 4
