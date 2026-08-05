"""Workout definitions for Tom's training plan."""

from __future__ import annotations

from typing import Any

# duration_minutes and distance_meters must be whole integers — decimals crash
# the COROS app when editing interval workouts.


def _open_run(name: str, minutes: int, *, sport_type: int = 101) -> dict[str, Any]:
    """Open / no-target run placeholder for races and unstructured sessions."""
    return {
        "name": name,
        "kind": "run",
        "sport_type": sport_type,
        "intensity_type": 0,
        "steps": [{"name": "Open — run to feel", "duration_minutes": minutes}],
    }


def _distance_run(
    name: str,
    meters: int,
    *,
    step_name: str = "Easy run",
    sport_type: int = 100,
) -> dict[str, Any]:
    """Run with a distance target (watch stops at metres, not minutes)."""
    return {
        "name": name,
        "kind": "run",
        "sport_type": sport_type,
        "intensity_type": 0,
        "steps": [{"name": step_name, "distance_meters": meters}],
    }


def _tempo_session(name: str, tempo_min: int, pace: str) -> dict[str, Any]:
    """10' easy + N' tempo + 5' cool — matches plan day-notes."""
    return {
        "name": name,
        "kind": "run",
        "sport_type": 100,
        "intensity_type": 0,
        "steps": [
            {"name": "Easy warmup", "duration_minutes": 10},
            {"name": f"Tempo — {pace}", "duration_minutes": tempo_min},
            {"name": "Easy cooldown", "duration_minutes": 5},
        ],
    }


def _fartlek_session(
    name: str,
    *,
    surge_min: int,
    easy_min: int,
    repeats: int,
    extra_surge_min: int = 0,
) -> dict[str, Any]:
    """10' easy + surge/easy blocks + 5' cool — 1–3 min surges at L6–L8."""
    steps: list[dict[str, Any]] = [
        {"name": "Easy warmup", "duration_minutes": 10},
        {
            "repeat": repeats,
            "steps": [
                {"name": f"Surge L6–L8 — {surge_min}'", "duration_minutes": surge_min},
                {"name": f"Easy jog — {easy_min}'", "duration_minutes": easy_min},
            ],
        },
    ]
    if extra_surge_min:
        steps.append(
            {"name": f"Surge L6–L8 — {extra_surge_min}'", "duration_minutes": extra_surge_min},
        )
    steps.append({"name": "Easy cooldown", "duration_minutes": 5})
    return {
        "name": name,
        "kind": "run",
        "sport_type": 100,
        "intensity_type": 0,
        "steps": steps,
    }


_COOPER_METERS = 2414  # 1.5 miles


WORKOUTS: dict[str, dict[str, Any]] = {
    "easy_3k": _distance_run("Easy 3K", 3000),
    "easy_4k": _distance_run("Easy 4K", 4000),
    "easy_5k": _distance_run("Easy 5K", 5000),
    "easy_6k": {
        "name": "Easy 6K + 5 strides",
        "kind": "run",
        "sport_type": 100,
        "intensity_type": 0,
        "steps": [
            {
                "kind": "training",
                "name": "Easy run",
                "target_type": "distance",
                "target_distance_meters": 6000,
            },
            {
                "repeat": 5,
                "name": "Strides",
                "steps": [
                    {
                        "kind": "training",
                        "name": "Stride",
                        "target_type": "time",
                        "target_duration_seconds": 22,
                    },
                    {
                        "kind": "rest",
                        "name": "Recovery jog",
                        "target_type": "time",
                        "target_duration_seconds": 75,
                    },
                ],
            },
        ],
    },
    "easy_10k": _distance_run("Easy 10K", 10000),
    "easy_8k": _distance_run("Easy 8K — conversational", 8000),
    "progression_8k": {
        "name": "Progression 8K — 5K easy / 3K steady",
        "kind": "run",
        "sport_type": 100,
        "intensity_type": 0,
        "steps": [
            {"name": "Easy", "distance_meters": 5000},
            {"name": "Steady effort", "distance_meters": 3000},
        ],
    },
    "progression_10k": {
        "name": "Progression 10K — 6K easy / 4K steady",
        "kind": "run",
        "sport_type": 100,
        "intensity_type": 0,
        "steps": [
            {"name": "Easy", "distance_meters": 6000},
            {"name": "Steady effort", "distance_meters": 4000},
        ],
    },
    "build_8k": {
        "name": "Build 8K — 5K easy / 1K moderate / 1K hard / 1K push",
        "kind": "run",
        "sport_type": 100,
        "intensity_type": 0,
        "steps": [
            {"name": "Easy 5:30-5:45/km", "distance_meters": 5000},
            {"name": "Moderate 4:50-5:00/km", "distance_meters": 1000},
            {"name": "Hard 4:30-4:40/km", "distance_meters": 1000},
            {"name": "Push 4:15-4:25/km", "distance_meters": 1000},
        ],
    },
    "walk_jog_recovery": {
        "name": "Walk/jog recovery — 2:1",
        "kind": "run",
        "sport_type": 100,
        "intensity_type": 0,
        "steps": [
            {"name": "Easy jog warmup", "duration_minutes": 5},
            {
                "repeat": 10,
                "steps": [
                    {"name": "Walk", "duration_minutes": 2},
                    {"name": "Very easy jog", "duration_minutes": 1},
                ],
            },
            {"name": "Walk cooldown", "duration_minutes": 5},
        ],
    },
    "run_club_5k": _distance_run("Run club — easy 5K", 5000),
    "run_club_6k": _distance_run("Run club — easy 6K", 6000),
    "run_club_8k": _distance_run("Run club — easy 8K", 8000),
    "race_maverick": _open_run("Maverick Peaks 10K", 75),
    "race_calver": _open_run("Calver Peak Fell Race 8K", 70),
    "race_outer_projects_12k": _open_run("Outer Projects 12K social run", 75),
    "race_bakewell": _open_run("Bakewell Pudding Race 10.4K", 80),
    "race_bamford": _open_run("Bamford Carnival Fell ~7.2K", 60),
    "race_stoney": _open_run("Stoney Middleton Fell ~8.5K", 65),
    "race_open": _open_run("Race day — open", 90),
    "tempo_7k": {
        "name": "7K Tempo Run",
        "kind": "run",
        "sport_type": 100,
        "intensity_type": 0,
        "steps": [
            {"name": "Warmup", "duration_minutes": 10},
            {"name": "Tempo effort", "distance_meters": 7000},
            {"name": "Cooldown", "duration_minutes": 10},
        ],
    },
    "tempo_8k": {
        "name": "8K Tempo — 3x8min",
        "kind": "run",
        "sport_type": 100,
        "intensity_type": 0,
        "steps": [
            {"name": "Warmup", "duration_minutes": 10},
            {
                "repeat": 3,
                "steps": [
                    {"name": "Tempo 8min", "duration_minutes": 8},
                    {"name": "Jog recovery", "duration_minutes": 2},
                ],
            },
            {"name": "Cooldown", "duration_minutes": 10},
        ],
    },
    "tempo_6k": {
        "name": "6K Tempo — taper",
        "kind": "run",
        "sport_type": 100,
        "intensity_type": 0,
        "steps": [
            {"name": "Warmup", "duration_minutes": 10},
            {"name": "Tempo effort", "distance_meters": 6000},
            {"name": "Cooldown", "duration_minutes": 10},
        ],
    },
    "bac_intervals": {
        "name": "BAC — 4x500,300,200,100",
        "kind": "run",
        "sport_type": 100,
        "intensity_type": 0,
        "steps": [
            {"name": "Warmup", "duration_minutes": 15},
            {
                "repeat": 4,
                "steps": [
                    {"name": "500m effort", "distance_meters": 500},
                    {"name": "Recovery", "duration_minutes": 2},
                    {"name": "300m effort", "distance_meters": 300},
                    {"name": "Recovery", "duration_minutes": 1},
                    {"name": "200m effort", "distance_meters": 200},
                    {"name": "Recovery", "duration_minutes": 1},
                    {"name": "100m sprint", "distance_meters": 100},
                    {"name": "Full recovery", "duration_minutes": 2},
                ],
            },
            {"name": "Cooldown", "duration_minutes": 10},
        ],
    },
    "bac_hill_6x800": {
        "name": "BAC — 6x800m hill reps",
        "kind": "run",
        "sport_type": 100,
        "intensity_type": 0,
        "steps": [
            {"name": "Warmup", "duration_minutes": 15},
            {
                "repeat": 6,
                "steps": [
                    {"name": "Hard uphill", "distance_meters": 800},
                    {"name": "Recovery to bottom", "target_type": "open"},
                ],
            },
            {"name": "Cooldown", "duration_minutes": 10},
        ],
    },
    "bac_threshold_4x6": {
        "name": "BAC — 4x6min threshold",
        "kind": "run",
        "sport_type": 100,
        "intensity_type": 0,
        "steps": [
            {"name": "Warmup", "duration_minutes": 10},
            {
                "repeat": 4,
                "steps": [
                    {"name": "Threshold", "duration_minutes": 6},
                    {"name": "Recovery", "duration_minutes": 2},
                ],
            },
            {"name": "Cooldown", "duration_minutes": 10},
        ],
    },
    # Fire service MSFT (20m bleep) — use a phone app for the beeps; watch paces the session.
    # Speeds: L6 11.0km/h (5:27/km) · L7 11.5 (5:13/km) · L8 12.0 (5:00/km) · L9 12.5 (4:48/km)
    "bleep_practice": {
        "name": "Bleep practice — full test (L8=5:00/km)",
        "kind": "run",
        "sport_type": 100,
        "intensity_type": 0,
        "steps": [
            {"name": "Easy jog", "duration_minutes": 5},
            {
                "repeat": 4,
                "steps": [
                    {"name": "Easy 20m turn — light only", "duration_minutes": 1},
                    {"name": "Walk recover", "duration_minutes": 1},
                ],
            },
            {
                "name": "Full MSFT — Spotify L1→fail · aim 7.0+",
                "duration_minutes": 15,
            },
            {"name": "Easy jog cooldown", "duration_minutes": 5},
        ],
    },
    "bleep_test": _open_run(
        "Fire service bleep — 8.8+ (L8=5:00/km)", 30, sport_type=100
    ),
    "shuttle_pace": {
        "name": "Speed intervals — L7–8 (5:13–5:00/km)",
        "kind": "run",
        "sport_type": 100,
        "intensity_type": 0,
        "steps": [
            {"name": "Easy jog", "duration_minutes": 8},
            {"name": "Strides ×4", "duration_minutes": 2},
            {
                "repeat": 4,
                "steps": [
                    {"name": "Hard L7 — 5:13/km", "duration_minutes": 1},
                    {"name": "Walk recover", "duration_minutes": 1},
                ],
            },
            {
                "repeat": 4,
                "steps": [
                    {"name": "Hard L8 — 5:00/km", "duration_minutes": 1},
                    {"name": "Walk recover", "duration_minutes": 1},
                ],
            },
            {"name": "Cooldown jog", "duration_minutes": 5},
        ],
    },
    # Lighter than shuttle_pace — Gower weekend sharpener / between quality days
    "shuttle_short": {
        "name": "Shuttle short — 4× L7 + 2× L8",
        "kind": "run",
        "sport_type": 100,
        "intensity_type": 0,
        "steps": [
            {"name": "Easy jog", "duration_minutes": 5},
            {
                "repeat": 4,
                "steps": [
                    {"name": "20m turn drill — smooth pivot", "duration_minutes": 1},
                    {"name": "Walk recover", "duration_minutes": 1},
                ],
            },
            {
                "repeat": 4,
                "steps": [
                    {"name": "Hard L7 — 5:13/km (~6.3s)", "duration_minutes": 1},
                    {"name": "Walk recover", "duration_minutes": 1},
                ],
            },
            {
                "repeat": 2,
                "steps": [
                    {"name": "Hard L8 — 5:00/km (6.0s)", "duration_minutes": 1},
                    {"name": "Walk recover", "duration_minutes": 1},
                ],
            },
            {"name": "Cooldown jog", "duration_minutes": 5},
        ],
    },
    "cooper_1_5_mile": {
        "name": "Cooper 1.5 mile — time trial",
        "kind": "run",
        "sport_type": 100,
        "intensity_type": 0,
        "steps": [
            {"name": "Easy jog warmup", "duration_minutes": 12},
            {
                "repeat": 3,
                "steps": [
                    {"name": "Stride — smooth pick-up", "duration_minutes": 1},
                    {"name": "Walk/jog recover", "duration_minutes": 1},
                ],
            },
            {
                "name": "Cooper 1.5 mile — even split ~5:00/km",
                "distance_meters": _COOPER_METERS,
            },
            {"name": "Easy jog cooldown", "duration_minutes": 10},
        ],
    },
    # Fartlek — 10' warm + surges + 5' cool (matches plan Tue sessions)
    "fartlek_20": _fartlek_session(
        "Fartlek 20' — varied pace", surge_min=2, easy_min=2, repeats=5,
    ),
    "fartlek_22": _fartlek_session(
        "Fartlek 22' — varied pace", surge_min=2, easy_min=2, repeats=5, extra_surge_min=2,
    ),
    "fartlek_25": _fartlek_session(
        "Fartlek 25' — varied pace", surge_min=3, easy_min=2, repeats=5,
    ),
    # Tempo — 10' easy + N' threshold + 5' cool (matches plan Fri sessions)
    "tempo_20": _tempo_session("Tempo 20' — threshold", 20, "~5:20–5:30/km"),
    "tempo_22": _tempo_session("Tempo 22' — threshold", 22, "~5:15–5:25/km"),
    "tempo_25": _tempo_session("Tempo 25' — threshold", 25, "~5:10–5:20/km"),
    # Technique only — not to failure
    "shuttle_turns": {
        "name": "Shuttle turns — technique",
        "kind": "run",
        "sport_type": 100,
        "intensity_type": 0,
        "steps": [
            {"name": "Easy jog", "duration_minutes": 5},
            {
                "repeat": 4,
                "steps": [
                    {"name": "Easy 20m — build gradually", "duration_minutes": 1},
                    {"name": "Walk recover", "duration_minutes": 1},
                ],
            },
            {
                "repeat": 12,
                "steps": [
                    {"name": "20m turn drill — smooth pivot", "duration_minutes": 1},
                    {"name": "Walk recover", "duration_minutes": 1},
                ],
            },
            {"name": "Easy jog", "duration_minutes": 5},
        ],
    },
    # Skip early easy levels — more time near L7–8
    "bleep_partial": _open_run(
        "Mini bleep — start L5 → fail", 18, sport_type=100
    ),
    "easy_shuttles_l7": {
        "name": "Easy shuttles — 8× L7",
        "kind": "run",
        "sport_type": 100,
        "intensity_type": 0,
        "steps": [
            {"name": "Easy jog", "duration_minutes": 5},
            {
                "repeat": 8,
                "steps": [
                    {"name": "20m @ L7 — 5:13/km (~6.3s)", "duration_minutes": 1},
                    {"name": "Walk recover", "duration_minutes": 1},
                ],
            },
            {"name": "Easy jog", "duration_minutes": 5},
        ],
    },
    "easy_5k_shuttle": {
        "name": "Easy 5K + L7 shuttle finisher",
        "kind": "run",
        "sport_type": 100,
        "intensity_type": 0,
        "steps": [
            {"name": "Easy 5K", "distance_meters": 5000},
            {
                "repeat": 8,
                "steps": [
                    {"name": "20m @ L7 — 5:13/km (~6.3s)", "duration_minutes": 1},
                    {"name": "Walk recover", "duration_minutes": 1},
                ],
            },
        ],
    },
    "easy_4k_shuttle": {
        "name": "Easy 4K + L7 shuttle finisher",
        "kind": "run",
        "sport_type": 100,
        "intensity_type": 0,
        "steps": [
            {"name": "Easy 4K", "distance_meters": 4000},
            {
                "repeat": 8,
                "steps": [
                    {"name": "20m @ L7 — 5:13/km (~6.3s)", "duration_minutes": 1},
                    {"name": "Walk recover", "duration_minutes": 1},
                ],
            },
        ],
    },
    "5k_time_trial": {
        "name": "5K Time Trial",
        "kind": "run",
        "sport_type": 100,
        "intensity_type": 0,
        "steps": [
            {"name": "Warmup", "duration_minutes": 10},
            {"name": "5K max effort", "distance_meters": 5000},
            {"name": "Cooldown", "duration_minutes": 10},
        ],
    },
    "long_10k": _distance_run(
        "Long Run 10K easy", 10000, step_name="Easy long run", sport_type=101
    ),
    "long_12k": _distance_run(
        "Long Run 12K easy", 12000, step_name="Easy long run", sport_type=101
    ),
    "long_14k": _distance_run(
        "Long Run 14K easy", 14000, step_name="Easy long run", sport_type=101
    ),
    "long_run": {
        "name": "Easy Long Run",
        "kind": "run",
        "sport_type": 101,
        "intensity_type": 0,
        "steps": [{"name": "Easy long run", "duration_minutes": 75}],
    },
    "long_16k": _distance_run(
        "Long Run 16K easy", 16000, step_name="Easy long run", sport_type=101
    ),
    "strength_full_body": {
        "name": "Strength — full body",
        "kind": "strength",
        "strength_preset": "full_body",
        "circuit_sets": 1,
    },
    "strength_wk1": {
        "name": "Strength — Foundation (WK1)",
        "kind": "strength",
        "strength_preset": "wk1",
        "circuit_sets": 3,
    },
    "strength_wk2": {
        "name": "Strength — Build (WK2)",
        "kind": "strength",
        "strength_preset": "wk2",
        "circuit_sets": 3,
    },
    "strength_wk3": {
        "name": "Strength — Intensity (WK3)",
        "kind": "strength",
        "strength_preset": "wk3",
        "circuit_sets": 4,
    },
    "strength_wk4": {
        "name": "Strength — Taper (WK4)",
        "kind": "strength",
        "strength_preset": "wk4",
        "circuit_sets": 3,
    },
    "strength_wk5": {
        "name": "Strength — Light (WK5)",
        "kind": "strength",
        "strength_preset": "wk5",
        "circuit_sets": 2,
    },
}
