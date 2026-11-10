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
    # --- added for the rotating session types (lower / push-pull / carry) ---
    "deadlift": {
        "origin_id": "425832295182811136",
        "name": "T1067",
        "overview": "sid_strength_deadlifts",
    },
    "single_leg_rdl": {
        "origin_id": "426612348485287936",
        "name": "T1144",
        "overview": "sid_strength_one_leg_deadlifts_and_knee_lifting",
    },
    "split_squat": {
        "origin_id": "425832124457861121",
        "name": "T1064",
        "overview": "sid_strength_dumbbell_lunges",
    },
    "step_up": {
        "origin_id": "425832054396207104",
        "name": "T1060",
        "overview": "sid_strength_step_up_jumps",
    },
    "band_lateral_walk": {
        "origin_id": "425845955863166977",
        "name": "T1103",
        "overview": "sid_strength_lateral_band_walks",
    },
    "floor_press": {
        "origin_id": "425831217146019840",
        "name": "T1041",
        "overview": "sid_strength_bench_press",
    },
    "band_face_pull": {
        "origin_id": "425867974013009920",
        "name": "T1106",
        "overview": "sid_strength_reverse_flys_with_bands",
    },
    "db_shrug": {
        "origin_id": "425831979771150336",
        "name": "T1058",
        "overview": "sid_strength_dumbbell_shrugs",
    },
    "db_side_bend": {
        "origin_id": "425827936327876608",
        "name": "T1011",
        "overview": "sid_strength_dumbbell_side_bends",
    },
    "plank": {
        "origin_id": "425827856334110721",
        "name": "T1010",
        "overview": "sid_strength_planks",
    },
    "side_plank": {
        "origin_id": "426611709340467200",
        "name": "T1143",
        "overview": "sid_strength_side_bridge_wing_arm_and_swing_leg",
    },
    "bicycle_crunch": {
        "origin_id": "425832906678779905",
        "name": "T1076",
        "overview": "sid_strength_bicycle_crunches",
    },
    "burpee": {
        "origin_id": "425827765602926593",
        "name": "T1007",
        "overview": "sid_strength_burpees",
    },
    "mountain_climber": {
        "origin_id": "425844786826756096",
        "name": "T1079",
        "overview": "sid_strength_mountain_climbers",
    },
    "squat_jump": {
        "origin_id": "425844691263733761",
        "name": "T1078",
        "overview": "sid_strength_squat_jumps",
    },
    # --- added for job-stiffness support (pull bias + mobility block) ---
    "dead_bug": {
        "origin_id": "469654335807209472",
        "name": "T1243",
        "overview": "sid_strength_dead_bug",
    },
    "bird_dog": {
        "origin_id": "469654452845068288",
        "name": "T1249",
        "overview": "sid_strength_bird_dog_balance",
    },
    "prone_y": {
        "origin_id": "469655003674624000",
        "name": "T1278",
        "overview": "sid_strength_prone_ys",
    },
    "thoracic_rotation": {
        "origin_id": "469654431907102720",
        "name": "T1248",
        "overview": "sid_strength_thoracic_spine_rotation",
    },
    "cat_cow": {
        "origin_id": "469646932625768448",
        "name": "T1234",
        "overview": "sid_strength_cat_cow_stretch",
    },
    "glute_bridge_hold": {
        "origin_id": "469646833841520640",
        "name": "T1229",
        "overview": "sid_strength_glute_bridge_hold",
    },
    "chest_stretch": {
        "origin_id": "469654402916073472",
        "name": "T1247",
        "overview": "sid_strength_chest_stretch",
    },
    "lunge_stretch": {
        "origin_id": "469654938176372736",
        "name": "T1274",
        "overview": "sid_strength_lunge_stretch",
    },
    "single_leg_bridge": {
        "origin_id": "426801473612070912",
        "name": "T1160",
        "overview": "sid_strength_single_leg_bridge",
    },
    "clamshell": {
        "origin_id": "469656606502731776",
        "name": "T1317",
        "overview": "sid_strength_clamshell",
    },
    "prone_cobra": {
        "origin_id": "469646741768159232",
        "name": "T1223",
        "overview": "sid_strength_prone_cobra",
    },
}

# target_type: 2 = time (seconds), 3 = reps
ROUND_REST_SECONDS = 60


def _timed_station(
    key: str,
    *,
    work_seconds: int,
    rest_seconds: int,
    weight_kg: float | None = None,
) -> dict[str, Any]:
    block: dict[str, Any] = {
        "key": key,
        "target_type": 2,
        "target_value": work_seconds,
        "sets": 1,
        "rest_seconds": rest_seconds,
    }
    if weight_kg is not None:
        block["weight_kg"] = weight_kg
    return block


def _each_side(
    key: str,
    *,
    work_seconds: int,
    rest_after: int,
    switch_rest: int = 5,
) -> list[dict[str, Any]]:
    """Two slots, one per side. A short gap to swap, then the rest after the pair."""
    return [
        _timed_station(key, work_seconds=work_seconds, rest_seconds=switch_rest),
        _timed_station(key, work_seconds=work_seconds, rest_seconds=rest_after),
    ]


def _circuit(
    *,
    goblet: float = 12.5,
    rdl: float = 12.5,
    press: float = 12.5,
    row: float = 12.5,
    carry: float = 12.5,
    work_seconds: int = 40,
    rest_seconds: int = 20,
    carry_seconds: int = 45,
) -> list[dict[str, Any]]:
    """One circuit lap — all stations for time (matches training_plan.html STR_WEEKS)."""
    row_work = work_seconds * 2  # sided: L then R in one block
    return [
        _timed_station(
            "goblet_squat",
            work_seconds=work_seconds,
            rest_seconds=rest_seconds,
            weight_kg=goblet,
        ),
        _timed_station(
            "romanian_deadlift",
            work_seconds=work_seconds,
            rest_seconds=rest_seconds,
            weight_kg=rdl,
        ),
        _timed_station(
            "overhead_press",
            work_seconds=work_seconds,
            rest_seconds=rest_seconds,
            weight_kg=press,
        ),
        _timed_station(
            "dumbbell_row",
            work_seconds=row_work,
            rest_seconds=rest_seconds,
            weight_kg=row,
        ),
        _timed_station("press_ups", work_seconds=work_seconds, rest_seconds=rest_seconds),
        _timed_station("calf_raise", work_seconds=work_seconds, rest_seconds=rest_seconds),
        _timed_station(
            "farmers_carry",
            work_seconds=carry_seconds,
            rest_seconds=ROUND_REST_SECONDS,
            weight_kg=carry,
        ),
    ]


# ── Block phases (WK1..WK5) — timing/load knob shared by every session type.
# Matches the original training_plan.html STR_WEEKS timings so the conditioning
# circuit is byte-for-byte unchanged from the old wk1..wk5 presets.
PHASES: dict[int, dict[str, Any]] = {
    1: {"work": 40, "rest": 20, "carry": 45, "heavy": 12.5, "light": 12.5},
    2: {"work": 45, "rest": 15, "carry": 50, "heavy": 12.5, "light": 12.5},
    3: {"work": 45, "rest": 15, "carry": 55, "heavy": 15.0, "light": 12.5},
    4: {"work": 40, "rest": 20, "carry": 50, "heavy": 15.0, "light": 12.5},
    5: {"work": 30, "rest": 30, "carry": 40, "heavy": 12.5, "light": 12.5},
}


def _lower_circuit(p: dict[str, Any]) -> list[dict[str, Any]]:
    """One lap — squat / hinge / single-leg / calves / glute-med / core."""
    w, r = p["work"], p["rest"]
    return [
        _timed_station("goblet_squat", work_seconds=w, rest_seconds=r, weight_kg=p["heavy"]),
        _timed_station("romanian_deadlift", work_seconds=w, rest_seconds=r, weight_kg=p["heavy"]),
        _timed_station("split_squat", work_seconds=w * 2, rest_seconds=r, weight_kg=p["light"]),
        _timed_station("step_up", work_seconds=w * 2, rest_seconds=r, weight_kg=p["light"]),
        _timed_station("calf_raise", work_seconds=w * 2, rest_seconds=r),
        _timed_station("band_lateral_walk", work_seconds=w, rest_seconds=r),
        _timed_station("dead_bug", work_seconds=w, rest_seconds=ROUND_REST_SECONDS),
    ]


def _pushpull_circuit(p: dict[str, Any]) -> list[dict[str, Any]]:
    """One lap — 2 push : 4 pull (overhead press kept for the fire-service tests,
    but the job already loads the shoulders overhead, so pulling leads)."""
    w, r = p["work"], p["rest"]
    return [
        _timed_station("overhead_press", work_seconds=w, rest_seconds=r, weight_kg=p["heavy"]),
        _timed_station("floor_press", work_seconds=w, rest_seconds=r, weight_kg=p["heavy"]),
        _timed_station("dumbbell_row", work_seconds=w, rest_seconds=r, weight_kg=p["heavy"]),
        _timed_station("dumbbell_row", work_seconds=w * 2, rest_seconds=r, weight_kg=p["heavy"]),
        _timed_station("band_face_pull", work_seconds=w, rest_seconds=r),
        _timed_station("prone_y", work_seconds=w, rest_seconds=r),
        _timed_station("side_plank", work_seconds=w * 2, rest_seconds=ROUND_REST_SECONDS),
    ]


def _carry_circuit(p: dict[str, Any]) -> list[dict[str, Any]]:
    """One lap — loaded carries, hinge, grip, climb (firefighter-specific)."""
    w, r, c = p["work"], p["rest"], p["carry"]
    return [
        _timed_station("farmers_carry", work_seconds=c, rest_seconds=r, weight_kg=p["heavy"]),
        _timed_station("farmers_carry", work_seconds=c * 2, rest_seconds=r, weight_kg=p["heavy"]),
        _timed_station("farmers_carry", work_seconds=c, rest_seconds=r, weight_kg=p["light"]),
        _timed_station("deadlift", work_seconds=w, rest_seconds=r, weight_kg=p["heavy"]),
        _timed_station("db_shrug", work_seconds=w, rest_seconds=r, weight_kg=p["heavy"]),
        _timed_station("step_up", work_seconds=w * 2, rest_seconds=r, weight_kg=p["light"]),
        _timed_station("db_side_bend", work_seconds=w * 2, rest_seconds=ROUND_REST_SECONDS,
                       weight_kg=p["light"]),
    ]


# Phase-rotated finisher for the conditioning circuit (replaces the old calf slot).
_COND_FINISHER = {1: "mountain_climber", 2: "squat_jump", 3: "burpee",
                  4: "squat_jump", 5: "mountain_climber"}


def _conditioning_circuit(phase: int, p: dict[str, Any]) -> list[dict[str, Any]]:
    """The original full-body circuit-for-time, calf slot swapped for a finisher."""
    w, r = p["work"], p["rest"]
    return [
        _timed_station("goblet_squat", work_seconds=w, rest_seconds=r, weight_kg=12.5),
        _timed_station("romanian_deadlift", work_seconds=w, rest_seconds=r, weight_kg=p["heavy"]),
        _timed_station("overhead_press", work_seconds=w, rest_seconds=r, weight_kg=p["heavy"]),
        _timed_station("dumbbell_row", work_seconds=w * 2, rest_seconds=r, weight_kg=p["heavy"]),
        _timed_station("press_ups", work_seconds=w, rest_seconds=r),
        _timed_station(_COND_FINISHER[phase], work_seconds=w, rest_seconds=r),
        _timed_station("farmers_carry", work_seconds=p["carry"], rest_seconds=ROUND_REST_SECONDS,
                       weight_kg=p["heavy"]),
    ]


def mobility_circuit() -> list[dict[str, Any]]:
    """~9 min neck/thoracic/hip mobility block — run mornings and after shift.

    Sided stations (thoracic rotation, hip-flexor lunge stretch) are doubled
    for L then R in one block, like the row/split-squat stations above.
    """
    return [
        _timed_station("cat_cow", work_seconds=45, rest_seconds=10),
        _timed_station("thoracic_rotation", work_seconds=60, rest_seconds=10),
        _timed_station("chest_stretch", work_seconds=45, rest_seconds=10),
        _timed_station("lunge_stretch", work_seconds=60, rest_seconds=10),
        _timed_station("glute_bridge_hold", work_seconds=40, rest_seconds=10),
        _timed_station("bird_dog", work_seconds=60, rest_seconds=10),
        _timed_station("dead_bug", work_seconds=45, rest_seconds=10),
        _timed_station("prone_y", work_seconds=40, rest_seconds=0),
    ]


def back_settle_circuit() -> list[dict[str, Any]]:
    """~11 min gentle, pain-free back settle for the acute phase (no loaded or core-bracing work)."""
    return [
        _timed_station("cat_cow", work_seconds=60, rest_seconds=15),
        _timed_station("thoracic_rotation", work_seconds=60, rest_seconds=15),
        _timed_station("lunge_stretch", work_seconds=60, rest_seconds=15),
        _timed_station("glute_bridge_hold", work_seconds=30, rest_seconds=20),
        _timed_station("glute_bridge_hold", work_seconds=30, rest_seconds=20),
        _timed_station("cat_cow", work_seconds=60, rest_seconds=0),
    ]


def back_rebuild_1_circuit() -> list[dict[str, Any]]:
    """10 min. Daily while it is still settling.

    One-sided moves get a slot each. The two-foot bridge stays as one slot.
    """
    strength = [
        _timed_station("glute_bridge_hold", work_seconds=50, rest_seconds=10),
        *_each_side("dead_bug", work_seconds=25, rest_after=10),
        *_each_side("bird_dog", work_seconds=25, rest_after=10),
    ]
    return [
        _timed_station("cat_cow", work_seconds=35, rest_seconds=10),
        *_each_side("thoracic_rotation", work_seconds=30, rest_after=10),
        *_each_side("lunge_stretch", work_seconds=30, rest_after=10),
        *strength,
        *strength,
        _timed_station("prone_y", work_seconds=25, rest_seconds=0),
    ]


def back_rebuild_2_circuit() -> list[dict[str, Any]]:
    """10 min, four days. One-leg bridge and clamshell, each side in its own slot."""
    strength = [
        *_each_side("single_leg_bridge", work_seconds=25, rest_after=10),
        *_each_side("dead_bug", work_seconds=20, rest_after=10),
        *_each_side("clamshell", work_seconds=20, rest_after=10),
        *_each_side("bird_dog", work_seconds=25, rest_after=10),
    ]
    second = [
        *_each_side("single_leg_bridge", work_seconds=25, rest_after=10),
        *_each_side("dead_bug", work_seconds=20, rest_after=10),
        *_each_side("clamshell", work_seconds=20, rest_after=10),
        *_each_side("bird_dog", work_seconds=25, rest_after=0),
    ]
    return [
        _timed_station("cat_cow", work_seconds=20, rest_seconds=0),
        *_each_side("thoracic_rotation", work_seconds=20, rest_after=10),
        *_each_side("lunge_stretch", work_seconds=20, rest_after=10),
        *strength,
        *second,
    ]


def back_rebuild_3_circuit() -> list[dict[str, Any]]:
    """10 min, four days. Same strength pairs, plus a short prone cobra."""
    strength = [
        *_each_side("single_leg_bridge", work_seconds=25, rest_after=10),
        *_each_side("clamshell", work_seconds=20, rest_after=10),
        *_each_side("bird_dog", work_seconds=25, rest_after=10),
        *_each_side("dead_bug", work_seconds=15, rest_after=10),
    ]
    return [
        *_each_side("thoracic_rotation", work_seconds=20, rest_after=10),
        *_each_side("lunge_stretch", work_seconds=20, rest_after=10),
        *strength,
        *strength,
        _timed_station("prone_cobra", work_seconds=30, rest_seconds=0),
    ]


def back_keep_circuit() -> list[dict[str, Any]]:
    """10 min, three days a week. Maintenance set, one slot per side."""
    strength = [
        *_each_side("single_leg_bridge", work_seconds=25, rest_after=10),
        *_each_side("clamshell", work_seconds=20, rest_after=10),
        *_each_side("bird_dog", work_seconds=25, rest_after=10),
        *_each_side("dead_bug", work_seconds=20, rest_after=10),
    ]
    return [
        _timed_station("cat_cow", work_seconds=20, rest_seconds=10),
        *_each_side("lunge_stretch", work_seconds=25, rest_after=10),
        *strength,
        *strength,
        _timed_station("prone_y", work_seconds=25, rest_seconds=0),
    ]


_SESSION_BUILDERS = {
    "lower": lambda phase, p: _lower_circuit(p),
    "pushpull": lambda phase, p: _pushpull_circuit(p),
    "carry": lambda phase, p: _carry_circuit(p),
    "conditioning": _conditioning_circuit,
}

# Presets aligned with training_plan.html STR_SESSIONS (Thu strength circuits).
# Legacy wk1..wk5 keys are kept as aliases for the conditioning circuit.
STRENGTH_PRESETS: dict[str, list[dict[str, Any]]] = {
    "full_body": _circuit(),
    "mobility": mobility_circuit(),
    "back_settle": back_settle_circuit(),
    "back_rebuild_1": back_rebuild_1_circuit(),
    "back_rebuild_2": back_rebuild_2_circuit(),
    "back_rebuild_3": back_rebuild_3_circuit(),
    "back_keep": back_keep_circuit(),
}
for _phase, _p in PHASES.items():
    STRENGTH_PRESETS[f"wk{_phase}"] = _conditioning_circuit(_phase, _p)
    for _session, _builder in _SESSION_BUILDERS.items():
        STRENGTH_PRESETS[f"{_session}_wk{_phase}"] = _builder(_phase, _p)


def build_strength_exercises(preset: str = "full_body", *, rounds: int = 1) -> list[dict[str, Any]]:
    """Expand a preset into COROS schedule_strength_workout exercise dicts.

    rounds repeats the full lap — COROS watch ignores top-level program sets for
    scheduled strength, so we duplicate stations instead of sets=3 on the program.
    """
    blocks = STRENGTH_PRESETS.get(preset)
    if not blocks:
        raise KeyError(f"Unknown strength preset: {preset}")

    laps = max(1, rounds)
    expanded: list[dict[str, Any]] = []
    for lap in range(laps):
        for idx, block in enumerate(blocks):
            entry_block = dict(block)
            # No rest after the final station of the final lap.
            if lap == laps - 1 and idx == len(blocks) - 1:
                entry_block["rest_seconds"] = 0
            expanded.append(entry_block)

    exercises: list[dict[str, Any]] = []
    for block in expanded:
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
