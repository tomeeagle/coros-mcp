"""Workout definitions for Tom's training plan."""

from __future__ import annotations

from typing import Any

# All duration_minutes must be whole integers — decimals crash the COROS app
# when editing interval workouts.


def _open_run(name: str, minutes: int, *, sport_type: int = 101) -> dict[str, Any]:
    """Open / no-target run placeholder for races and unstructured sessions."""
    return {
        "name": name,
        "kind": "run",
        "sport_type": sport_type,
        "intensity_type": 0,
        "steps": [{"name": "Open — run to feel", "duration_minutes": minutes}],
    }


WORKOUTS: dict[str, dict[str, Any]] = {
    "easy_3k": {
        "name": "Easy 3K — run streak",
        "kind": "run",
        "sport_type": 100,
        "intensity_type": 0,
        "steps": [{"name": "Easy run", "duration_minutes": 18}],
    },
    "easy_4k": {
        "name": "Easy 4K — run streak",
        "kind": "run",
        "sport_type": 100,
        "intensity_type": 0,
        "steps": [{"name": "Easy run", "duration_minutes": 24}],
    },
    "easy_5k": {
        "name": "Easy 5K — June streak",
        "kind": "run",
        "sport_type": 100,
        "intensity_type": 0,
        "steps": [{"name": "Easy run", "duration_minutes": 30}],
    },
    "run_club_5k": {
        "name": "Run club — easy 5K",
        "kind": "run",
        "sport_type": 100,
        "intensity_type": 0,
        "steps": [{"name": "Easy run", "duration_minutes": 30}],
    },
    "run_club_6k": {
        "name": "Run club — easy 6K",
        "kind": "run",
        "sport_type": 100,
        "intensity_type": 0,
        "steps": [{"name": "Easy run", "duration_minutes": 36}],
    },
    "run_club_8k": {
        "name": "Run club — easy 8K",
        "kind": "run",
        "sport_type": 100,
        "intensity_type": 0,
        "steps": [{"name": "Easy run", "duration_minutes": 48}],
    },
    "race_maverick": _open_run("Maverick Peaks 10K", 75),
    "race_calver": _open_run("Calver Peak Fell Race 8K", 70),
    "race_outer_projects_12k": _open_run("Outer Projects 12K social run", 75),
    "race_bakewell": _open_run("Bakewell Pudding Race 10.4K", 80),
    "race_love_trails": _open_run("Love Trails Race", 150),
    "race_open": _open_run("Race day — open", 90),
    "tempo_7k": {
        "name": "7K Tempo Run",
        "kind": "run",
        "sport_type": 100,
        "intensity_type": 0,
        "steps": [
            {"name": "Warmup", "duration_minutes": 10},
            {"name": "Tempo effort", "duration_minutes": 20},
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
            {"name": "Tempo effort", "duration_minutes": 15},
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
                    {"name": "500m effort", "duration_minutes": 2},
                    {"name": "Recovery", "duration_minutes": 2},
                    {"name": "300m effort", "duration_minutes": 1},
                    {"name": "Recovery", "duration_minutes": 1},
                    {"name": "200m effort", "duration_minutes": 1},
                    {"name": "Recovery", "duration_minutes": 1},
                    {"name": "100m sprint", "duration_minutes": 1},
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
                    {"name": "Hard uphill", "duration_minutes": 5},
                    {"name": "Recovery jog", "duration_minutes": 3},
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
    "5k_time_trial": {
        "name": "5K Time Trial",
        "kind": "run",
        "sport_type": 100,
        "intensity_type": 0,
        "steps": [
            {"name": "Warmup", "duration_minutes": 10},
            {"name": "5K max effort", "duration_minutes": 22},
            {"name": "Cooldown", "duration_minutes": 10},
        ],
    },
    "long_10k": {
        "name": "Long Run 10K easy",
        "kind": "run",
        "sport_type": 101,
        "intensity_type": 0,
        "steps": [{"name": "Easy long run", "duration_minutes": 65}],
    },
    "long_14k": {
        "name": "Long Run 14K easy",
        "kind": "run",
        "sport_type": 101,
        "intensity_type": 0,
        "steps": [{"name": "Easy long run", "duration_minutes": 90}],
    },
    "long_run": {
        "name": "Easy Long Run",
        "kind": "run",
        "sport_type": 101,
        "intensity_type": 0,
        "steps": [{"name": "Easy long run", "duration_minutes": 75}],
    },
    "long_16k": {
        "name": "Long Run 16K easy",
        "kind": "run",
        "sport_type": 101,
        "intensity_type": 0,
        "steps": [{"name": "Easy long run", "duration_minutes": 100}],
    },
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
        "name": "Strength — Race week (WK5)",
        "kind": "strength",
        "strength_preset": "wk5",
        "circuit_sets": 2,
    },
}
