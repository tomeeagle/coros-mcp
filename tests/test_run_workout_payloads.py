"""Watch-loadable run payloads used by workout_sync.

These pin the local run builder that schedule_run_workout sends to the watch.
"""

from coros_mcp.coros_api import (
    build_run_workout_payload,
    legacy_run_steps_to_run_steps,
)


def test_run_workout_uses_sport_type_1_and_step_kinds():
    legacy = [
        {"name": "Warmup", "duration_minutes": 10},
        {
            "repeat": 2,
            "steps": [
                {"name": "Tempo 8min", "duration_minutes": 8},
                {"name": "Jog recovery", "duration_minutes": 2},
            ],
        },
        {"name": "Cooldown", "duration_minutes": 10},
    ]
    payload = build_run_workout_payload("Test", legacy_run_steps_to_run_steps(legacy))
    assert payload["sportType"] == 1
    assert payload["simple"] is False
    non_group = [e for e in payload["exercises"] if not e.get("isGroup")]
    assert non_group[0]["exerciseType"] == 1  # warmup
    assert non_group[-1]["exerciseType"] == 3  # cooldown
    assert all(e.get("sportType") == 1 for e in payload["exercises"])
    assert all(e.get("overview", "").startswith("sid_run_") for e in non_group)

def test_run_workout_distance_steps_use_target_type_5():
    from workout_sync.workouts import WORKOUTS

    steps = WORKOUTS["easy_3k"]["steps"]
    payload = build_run_workout_payload(
        WORKOUTS["easy_3k"]["name"],
        legacy_run_steps_to_run_steps(steps),
    )
    main = [e for e in payload["exercises"] if not e.get("isGroup")][0]
    assert main["targetType"] == 5
    assert main["targetValue"] == 300_000  # 3 km in COROS centimeters
    assert main["targetDisplayUnit"] == 1  # km
    assert payload["targetType"] == 5
    assert payload["targetValue"] == 300_000
    assert payload["distanceDisplayUnit"] == 1

def test_easy_6k_includes_stride_interval_group():
    from workout_sync.workouts import WORKOUTS

    steps = WORKOUTS["easy_6k"]["steps"]
    payload = build_run_workout_payload(WORKOUTS["easy_6k"]["name"], steps)
    groups = [e for e in payload["exercises"] if e.get("isGroup")]
    assert len(groups) == 1
    assert groups[0]["sets"] == 5
    sub = [e for e in payload["exercises"] if not e.get("isGroup")]
    stride = [e for e in sub if e.get("name") == "Stride"][0]
    recovery = [e for e in sub if e.get("name") == "Recovery jog"][0]
    assert stride["targetType"] == 2
    assert stride["targetValue"] == 22
    assert recovery["exerciseType"] == 4  # rest

def test_bac_hill_recovery_is_open_target():
    from workout_sync.workouts import WORKOUTS

    steps = WORKOUTS["bac_hill_6x800"]["steps"]
    payload = build_run_workout_payload(
        WORKOUTS["bac_hill_6x800"]["name"],
        legacy_run_steps_to_run_steps(steps),
    )
    recovery = [
        e for e in payload["exercises"]
        if e.get("name") == "Recovery to bottom"
    ][0]
    assert recovery["targetType"] == 1
    assert recovery["targetValue"] == 0
    assert recovery["exerciseType"] == 4

def test_tempo_20_has_warmup_tempo_cooldown():
    from workout_sync.workouts import WORKOUTS

    steps = WORKOUTS["tempo_20"]["steps"]
    payload = build_run_workout_payload(
        WORKOUTS["tempo_20"]["name"],
        legacy_run_steps_to_run_steps(steps),
    )
    names = [e["name"] for e in payload["exercises"] if not e.get("isGroup")]
    assert names[0] == "Easy warmup"
    assert "Tempo" in names[1]
    assert names[-1] == "Easy cooldown"
    tempo = [e for e in payload["exercises"] if e.get("name", "").startswith("Tempo")][0]
    assert tempo["targetType"] == 2
    assert tempo["targetValue"] == 20 * 60

def test_shuttle_pace_400m_steps_have_pace_alerts():
    from workout_sync.workouts import WORKOUTS

    steps = WORKOUTS["shuttle_pace"]["steps"]
    payload = build_run_workout_payload(WORKOUTS["shuttle_pace"]["name"], steps)
    reps = [
        e for e in payload["exercises"]
        if e.get("name", "").startswith("400m @") and not e.get("isGroup")
    ]
    assert len(reps) == 2
    assert reps[0]["intensityType"] == 3
    assert reps[0]["intensityValue"] == 290
    assert reps[0]["intensityValueExtend"] == 295
    assert reps[0]["intensityDisplayUnit"] == 2
    assert reps[1]["intensityValue"] == 280
    assert reps[1]["intensityValueExtend"] == 285
    rec = [
        e for e in payload["exercises"]
        if e.get("name", "").startswith("Walk recovery") and not e.get("isGroup")
    ][0]
    assert rec["exerciseType"] == 4
    assert rec["targetValue"] == 90
    stride = [
        e for e in payload["exercises"]
        if e.get("name") == "Stride" and not e.get("isGroup")
    ][0]
    assert stride["targetValue"] == 20

def test_speed_200_400_has_pace_alerts():
    from workout_sync.workouts import WORKOUTS

    steps = WORKOUTS["speed_200_400"]["steps"]
    payload = build_run_workout_payload(WORKOUTS["speed_200_400"]["name"], steps)
    two = [
        e for e in payload["exercises"]
        if e.get("name", "").startswith("200m @") and not e.get("isGroup")
    ]
    four = [
        e for e in payload["exercises"]
        if e.get("name", "").startswith("400m @") and not e.get("isGroup")
    ]
    assert len(two) == 1
    assert len(four) == 1
    assert two[0]["intensityType"] == 3
    assert two[0]["intensityValue"] == 270
    assert two[0]["intensityValueExtend"] == 280
    assert four[0]["intensityValue"] == 285
    assert four[0]["intensityValueExtend"] == 295

def test_speed_pyramid_has_600_and_pace_alerts():
    from workout_sync.workouts import WORKOUTS

    steps = WORKOUTS["speed_pyramid"]["steps"]
    payload = build_run_workout_payload(WORKOUTS["speed_pyramid"]["name"], steps)
    six = [
        e for e in payload["exercises"]
        if e.get("name", "").startswith("600m @") and not e.get("isGroup")
    ]
    assert len(six) == 1
    assert six[0]["intensityValue"] == 270  # 4:30/km
    assert six[0]["intensityValueExtend"] == 280  # 4:40/km

def test_cooper_1_5_mile_has_strides_and_distance():
    from workout_sync.workouts import WORKOUTS

    steps = WORKOUTS["cooper_1_5_mile"]["steps"]
    payload = build_run_workout_payload(
        WORKOUTS["cooper_1_5_mile"]["name"],
        legacy_run_steps_to_run_steps(steps),
    )
    groups = [e for e in payload["exercises"] if e.get("isGroup")]
    assert groups[0]["sets"] == 3
    main = [
        e for e in payload["exercises"]
        if e.get("name", "").startswith("Cooper 1.5 mile")
    ][0]
    assert main["targetType"] == 5
    assert main["targetValue"] == 241_400  # 2414 m in COROS centimeters
