"""COROS strength exercise catalogue mapping."""

from __future__ import annotations

import asyncio
from typing import Any

import coros_api

# Catalogue IDs from list_exercises (sport_type=4). Re-run:
#   python -m workout_sync.strength --refresh
STRENGTH_CATALOG: dict[str, dict[str, str]] = {
    "goblet_squat": {
        "origin_id": "469656067215900672",
        "name": "T1301",
        "overview": "sid_strength_goblet_squat",
    },
    "romanian_deadlift": {
        "origin_id": "469656136203812864",
        "name": "T1305",
        "overview": "sid_strength_dumbbell_romanian_deadlift",
    },
    "overhead_press": {
        "origin_id": "469656005475745792",
        "name": "T1297",
        "overview": "sid_strength_arnold_press",
    },
    "dumbbell_row": {
        "origin_id": "425831875618193409",
        "name": "T1055",
        "overview": "sid_strength_dumbbell_row",
    },
    "press_ups": {
        "origin_id": "425827704936513536",
        "name": "T1004",
        "overview": "sid_strength_push_ups",
    },
    "calf_raise": {
        "origin_id": "425832417320943617",
        "name": "T1070",
        "overview": "sid_strength_standing_calf_raises",
    },
    "farmers_carry": {
        "origin_id": "469656430677508096",
        "name": "T1310",
        "overview": "sid_strength_farmers_walk",
    },
}

# target_type: 2 = time (seconds), 3 = reps
def _circuit(
    *,
    goblet: float = 12.5,
    rdl: float = 12.5,
    press: float = 12.5,
    row: float = 12.5,
    carry: float = 12.5,
    rounds: int = 3,
    carry_seconds: int = 45,
) -> list[dict[str, Any]]:
    """One round of the plan circuit (matches plan HTML STR_WEEKS)."""
    return [
        {"key": "goblet_squat", "target_type": 3, "target_value": 12, "sets": rounds, "rest_seconds": 20, "weight_kg": goblet},
        {"key": "romanian_deadlift", "target_type": 3, "target_value": 10, "sets": rounds, "rest_seconds": 20, "weight_kg": rdl},
        {"key": "overhead_press", "target_type": 3, "target_value": 10, "sets": rounds, "rest_seconds": 20, "weight_kg": press},
        {"key": "dumbbell_row", "target_type": 3, "target_value": 10, "sets": rounds, "rest_seconds": 20, "weight_kg": row},
        {"key": "press_ups", "target_type": 3, "target_value": 15, "sets": rounds, "rest_seconds": 20},
        {"key": "calf_raise", "target_type": 3, "target_value": 15, "sets": rounds, "rest_seconds": 20},
        {"key": "farmers_carry", "target_type": 2, "target_value": carry_seconds, "sets": rounds, "rest_seconds": 60, "weight_kg": carry},
    ]


# Presets aligned with plan_v1_8.html STR_WEEKS (Mon strength sessions)
STRENGTH_PRESETS: dict[str, list[dict[str, Any]]] = {
    "full_body": _circuit(),
    "wk1": _circuit(goblet=12.5, rdl=12.5, press=12.5, row=12.5, carry=12.5, rounds=3, carry_seconds=45),
    "wk2": _circuit(goblet=12.5, rdl=12.5, press=12.5, row=12.5, carry=12.5, rounds=3, carry_seconds=50),
    "wk3": _circuit(goblet=12.5, rdl=15.0, press=15.0, row=15.0, carry=15.0, rounds=4, carry_seconds=55),
    "wk4": _circuit(goblet=12.5, rdl=15.0, press=15.0, row=15.0, carry=15.0, rounds=3, carry_seconds=50),
    "wk5": _circuit(goblet=12.5, rdl=12.5, press=12.5, row=12.5, carry=12.5, rounds=2, carry_seconds=40),
}


def build_strength_exercises(preset: str = "full_body") -> list[dict[str, Any]]:
    """Expand a preset into COROS schedule_strength_workout exercise dicts."""
    blocks = STRENGTH_PRESETS.get(preset)
    if not blocks:
        raise KeyError(f"Unknown strength preset: {preset}")

    exercises: list[dict[str, Any]] = []
    for block in blocks:
        key = block["key"]
        cat = STRENGTH_CATALOG.get(key)
        if not cat:
            raise KeyError(f"Unknown strength exercise key: {key}")

        entry: dict[str, Any] = {
            "origin_id": cat["origin_id"],
            "name": cat["name"],
            "overview": cat["overview"],
            "target_type": block["target_type"],
            "target_value": int(block["target_value"]),
            "rest_seconds": int(block.get("rest_seconds", 60)),
            "sets": int(block.get("sets", 1)),
        }
        if "weight_kg" in block:
            entry["weight_kg"] = block["weight_kg"]
        exercises.append(entry)
    return exercises


async def refresh_catalog_from_api() -> dict[str, dict[str, str]]:
    """Fetch catalogue and match plan exercise keys by overview sid."""
    auth = coros_api.get_stored_auth()
    if not auth:
        raise RuntimeError("Not authenticated. Run: coros-mcp auth-web")

    overviews = {v["overview"]: k for k, v in STRENGTH_CATALOG.items()}
    items = await coros_api.fetch_exercises(auth, 4)
    found: dict[str, dict[str, str]] = {}

    for ex in items:
        overview = ex.get("overview") or ""
        key = overviews.get(overview)
        if not key:
            continue
        found[key] = {
            "origin_id": str(ex["id"]),
            "name": ex.get("name", ""),
            "overview": overview,
        }
    return found


def _print_catalog_table(catalog: dict[str, dict[str, str]]) -> None:
    for key in STRENGTH_CATALOG:
        row = catalog.get(key, {})
        oid = row.get("origin_id", "?")
        name = row.get("name", "?")
        print(f"  {key:22}  {oid:>20}  {name}")


async def _cli_refresh() -> None:
    found = await refresh_catalog_from_api()
    print("Resolved strength exercises:\n")
    _print_catalog_table(found)
    missing = set(STRENGTH_CATALOG) - set(found)
    if missing:
        print(f"\nMissing: {', '.join(sorted(missing))}")


if __name__ == "__main__":
    import sys

    if "--refresh" in sys.argv:
        asyncio.run(_cli_refresh())
    else:
        print("Usage: python -m workout_sync.strength --refresh")
