"""Parse Tom's training plan HTML into COROS-syncable schedules."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

MONTHS: dict[str, int] = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

DEFAULT_PLAN_PATH = Path(__file__).resolve().parent.parent / "training_plan.html"


@dataclass
class ParsedDay:
    yyyymmdd: str
    day_label: str
    run_text: str
    note_text: str
    workout_key: str | None
    skip_reason: str | None = None


@dataclass
class ParsedWeek:
    key: str
    label: str
    phase: str
    days: dict[str, list[str]] = field(default_factory=dict)
    skipped: list[ParsedDay] = field(default_factory=list)


@dataclass
class ParsedPlan:
    year: int
    weeks: dict[str, ParsedWeek]
    schedule: dict[str, list[str]]
    unmapped: list[ParsedDay]
    strength_mondays: dict[str, str]  # YYYYMMDD -> wk1..wk5


def _parse_plan_year(html: str) -> int:
    m = re.search(r"(\d{4})\s*$", html[:4000], re.MULTILINE)
    if m:
        return int(m.group(1))
    m = re.search(r"–\s*\d{1,2}\s+\w+\s+(\d{4})", html[:4000])
    if m:
        return int(m.group(1))
    return 2026


def _parse_month_token(token: str) -> int:
    key = token.strip().lower()[:3]
    if key not in MONTHS:
        raise ValueError(f"Unknown month: {token}")
    return MONTHS[key]


def _parse_week_dates(text: str) -> tuple[tuple[int, int], tuple[int, int]]:
    """Return ((start_month, start_day), (end_month, end_day)) for a week-dates span."""
    text = text.replace("–", "-").replace("—", "-").strip()
    # "29 Jun - 6 Jul" or "1-7 Jun" or "16-24 May"
    cross = re.match(
        r"(\d{1,2})\s+(\w+)\s*-\s*(\d{1,2})\s+(\w+)",
        text,
        re.I,
    )
    if cross:
        return (
            (_parse_month_token(cross.group(2)), int(cross.group(1))),
            (_parse_month_token(cross.group(4)), int(cross.group(3))),
        )
    single = re.match(r"(\d{1,2})\s*-\s*(\d{1,2})\s+(\w+)", text, re.I)
    if single:
        month = _parse_month_token(single.group(3))
        return ((month, int(single.group(1))), (month, int(single.group(2))))
    lone = re.match(r"^(\d{1,2})\s+(\w+)$", text, re.I)
    if lone:
        month = _parse_month_token(lone.group(2))
        day = int(lone.group(1))
        return ((month, day), (month, day))
    raise ValueError(f"Cannot parse week dates: {text!r}")


def _parse_day_label(
    label: str,
    week_start: tuple[int, int],
    week_end: tuple[int, int],
    year: int,
) -> date:
    """e.g. Tue 2, Wed 1 Jul, Sat 28"""
    label = re.sub(r"\s+", " ", label.strip())
    explicit = re.match(r"\w+\s+(\d{1,2})\s+(\w+)", label, re.I)
    if explicit:
        month = _parse_month_token(explicit.group(2))
        day = int(explicit.group(1))
        return date(year, month, day)

    m = re.match(r"\w+\s+(\d{1,2})", label, re.I)
    if not m:
        raise ValueError(f"Cannot parse day label: {label!r}")
    day = int(m.group(1))

    start_month, start_day = week_start
    end_month, end_day = week_end

    if start_month == end_month:
        return date(year, start_month, day)

    # Week spans two months: days >= start_day are in start_month, else end_month
    if day >= start_day:
        return date(year, start_month, day)
    return date(year, end_month, day)


def _slug_week(title: str, dates: str) -> str:
    m = re.search(r"Week\s+(\d+)", title, re.I)
    num = m.group(1) if m else "0"
    phase = re.sub(r"[^a-z0-9]+", "_", title.lower())
    phase = re.sub(r"^week_\d+_?", "", phase).strip("_")[:30]
    if phase:
        return f"week_{num}_{phase}"
    return f"week_{num}"


def _parse_strength_mondays(html: str, year: int) -> dict[str, str]:
    """STR_WEEKS in the HTML: Mon 1 Jun -> wk1."""
    out: dict[str, str] = {}
    for m in re.finditer(
        r"(\d+):\s*\{[^}]*?date:'([^']+)'",
        html,
        re.DOTALL,
    ):
        wk_num = m.group(1)
        date_str = m.group(2)  # Mon 1 Jun
        dm = re.search(r"(\d{1,2})\s+(\w+)", date_str)
        if not dm:
            continue
        d = date(year, _parse_month_token(dm.group(2)), int(dm.group(1)))
        out[d.strftime("%Y%m%d")] = f"wk{wk_num}"
    return out


def _bac_key_from_text(text: str) -> str | None:
    bac_rules: list[tuple[str, str]] = [
        (r"bac.*interval|4.×500.*300.*200.*100", "bac_intervals"),
        (r"bac.*hill|6.×800", "bac_hill_6x800"),
        (r"bac.*threshold|4.×6min", "bac_threshold_4x6"),
    ]
    for pat, key in bac_rules:
        if re.search(pat, text, re.I):
            return key
    if re.search(r"\bbac\b", text, re.I):
        return "bac_intervals"
    return None


def _primary_run_key(
    run_text: str,
    note_text: str,
    yyyymmdd: str,
    strength_mondays: dict[str, str],
) -> tuple[str | None, str | None]:
    """Map the main run-cell session (single key)."""
    text = run_text.strip().lower()
    note = note_text.lower()

    if not text or text in ("—", "-"):
        return None, "empty"

    if re.search(r"^rest|^full rest", text, re.I):
        return None, "empty"

    combined = f"{text} {note}"

    if re.search(r"outer projects", combined, re.I):
        return "race_outer_projects_12k", None
    if re.search(r"social trail run", text, re.I):
        return "race_outer_projects_12k", None

    if re.search(r"bakewell pudding|pudding race", text, re.I):
        return "race_bakewell", None

    for pat, key in (
        (r"bamford carnival", "race_bamford"),
        (r"stoney middleton", "race_stoney"),
    ):
        if re.search(pat, text, re.I):
            return key, None

    race_rules: list[tuple[str, str]] = [
        (r"calver peak|calver fell race", "race_calver"),
        (r"7:30pm start", "race_calver"),
        (r"maverick", "race_maverick"),
        (r"race day|^race —", "race_open"),
    ]
    for pat, key in race_rules:
        if re.search(pat, text, re.I) or re.search(pat, note, re.I):
            return key, None

    skip_patterns = (
        r"travel",
        r"drive",
        r"festival",
        r"arrive",
        r"group runs/experiences",
        r"recovery runs",
        r"easy run/experience",
    )
    for pat in skip_patterns:
        if re.search(pat, text):
            return None, "rest_or_event"

    if re.search(r"run club", text):
        if re.search(r"6k", text):
            return "run_club_6k", None
        if re.search(r"5k", text):
            return "run_club_5k", None
        return "run_club_8k", None

    if "dumbbell strength" in text or ("strength" in note and "💪" in note_text):
        wk_m = re.search(r"strength\s+wk(\d+)", note, re.I)
        preset = f"wk{wk_m.group(1)}" if wk_m else strength_mondays.get(yyyymmdd, "wk1")
        return f"strength_{preset}", None

    bac_only = _bac_key_from_text(text)
    if bac_only and re.search(r"^bac\b", text.strip(), re.I):
        return bac_only, None

    rules: list[tuple[str, str]] = [
        (r"long run 16k", "long_16k"),
        (r"long run 14k", "long_14k"),
        (r"long run 12k", "long_12k"),
        (r"long run 10k", "long_10k"),
        (r"build 8k|5k easy.*1k moderate.*1k hard.*1k push", "build_8k"),
        (r"progression 10k|6k easy.*4k steady", "progression_10k"),
        (r"progression 8k|5k easy.*3k steady", "progression_8k"),
        (r"fire service bleep|bleep test.*8\.8|bleep test day", "bleep_test"),
        (r"bleep partial|start l5|start level 5", "bleep_partial"),
        (r"bleep practice|full test to failure|msft practice|full test \(l8", "bleep_practice"),
        (r"easy 5k \+ l7|easy 5k \+ shuttle|l7 shuttle finisher", "easy_5k_shuttle"),
        (r"shuttle turns|turn drill|technique", "shuttle_turns"),
        (r"shuttle pace|20m turns|shuttle intervals", "shuttle_pace"),
        (r"easy 10k", "easy_10k"),
        (r"easy 8k", "easy_8k"),
        (r"easy 6k|6k easy", "easy_6k"),
        (r"easy 5k", "easy_5k"),
        (r"3.×8min tempo|3×8min tempo", "tempo_8k"),
        (r"6k.*15min tempo", "tempo_6k"),
        (r"7k tempo|7k — 10min easy|7k tempo", "tempo_7k"),
        (r"easy 4k.*stride", "easy_4k"),
        (r"easy 4k|easy 3-4k", "easy_4k"),
        (r"easy 3k|streak.*3k", "easy_3k"),
        (r"easy 5k|streak.*5k", "easy_5k"),
    ]
    for pat, key in rules:
        if re.search(pat, text, re.I):
            return key, None

    return None, f"unmapped: {run_text[:60]}"


def _is_run_workout_key(key: str) -> bool:
    return key.startswith(
        (
            "bac_",
            "tempo_",
            "easy_",
            "long_",
            "run_club_",
            "race_",
            "progression_",
            "build_",
            "bleep_",
            "shuttle_",
        ),
    )


def _single_run_per_day(keys: list[str]) -> list[str]:
    """At most one run per calendar day; strength/races stay as mapped."""
    if len(keys) <= 1:
        return keys
    runs = [k for k in keys if _is_run_workout_key(k)]
    if len(runs) <= 1:
        return keys
    non_runs = [k for k in keys if not _is_run_workout_key(k)]
    bac = [k for k in runs if k.startswith("bac_")]
    chosen = bac[0] if bac else runs[0]
    return non_runs + [chosen] if non_runs else [chosen]


def _map_run_to_workouts(
    run_text: str,
    note_text: str,
    yyyymmdd: str,
    strength_mondays: dict[str, str],
) -> tuple[list[str], str | None]:
    """Return workout keys for a day (max one run; BAC wins if note says 6pm)."""
    keys: list[str] = []
    primary, skip = _primary_run_key(run_text, note_text, yyyymmdd, strength_mondays)
    if skip and skip != "empty":
        if skip.startswith("unmapped") or skip == "rest_or_event":
            return [], skip
    if primary:
        keys.append(primary)

    combined = f"{run_text} {note_text}"
    if re.search(r"bac\s*6pm|bac\s*6\s*pm", combined, re.I) or (
        re.search(r"\bBAC\b", note_text) and "6pm" in note_text.lower()
    ):
        bac = _bac_key_from_text(combined)
        if bac:
            keys = [bac] if _is_run_workout_key(primary or "") else keys + [bac]
    elif _bac_key_from_text(run_text) and not re.search(r"^rest", run_text, re.I):
        bac = _bac_key_from_text(run_text)
        if bac and bac not in keys:
            keys = [bac]

    if primary and primary.startswith("strength_"):
        post_strength: str | None = None
        if re.search(r"easy 6k|6k easy", combined, re.I):
            post_strength = "easy_6k"
        elif re.search(r"easy 3k|3k easy|\+ easy", combined, re.I):
            post_strength = "easy_3k"
        if post_strength and post_strength not in keys:
            keys.append(post_strength)

    keys = _single_run_per_day(keys)

    if keys:
        return keys, None
    if skip == "empty":
        return [], skip
    return [], skip


def _map_run_to_workout(
    run_text: str,
    note_text: str,
    yyyymmdd: str,
    strength_mondays: dict[str, str],
) -> tuple[str | None, str | None]:
    """Backward-compatible single-key mapper (first session only)."""
    keys, skip = _map_run_to_workouts(run_text, note_text, yyyymmdd, strength_mondays)
    if keys:
        return keys[0], None
    return None, skip


def parse_plan_html(path: Path | None = None) -> ParsedPlan:
    plan_path = path or DEFAULT_PLAN_PATH
    html = plan_path.read_text(encoding="utf-8")
    year = _parse_plan_year(html)
    strength_mondays = _parse_strength_mondays(html, year)
    weeks, schedule, unmapped = _parse_week_blocks_ordered(html, year, strength_mondays)

    return ParsedPlan(
        year=year,
        weeks=weeks,
        schedule=schedule,
        unmapped=unmapped,
        strength_mondays=strength_mondays,
    )


def _iter_week_block_chunks(html: str):
    """Yield inner HTML of each top-level week-block (handles nested divs)."""
    marker = '<div class="week-block'
    end_markers = ('<div class="week-block', "<!-- WEIGHT", "<hr ")
    pos = 0
    while True:
        start = html.find(marker, pos)
        if start < 0:
            return
        close = html.find(">", start)
        content_start = close + 1 if close >= 0 else start + len(marker)
        next_starts = [html.find(m, content_start) for m in end_markers]
        next_starts = [i for i in next_starts if i >= 0]
        end = min(next_starts) if next_starts else len(html)
        yield html[content_start:end]
        pos = end


def _parse_week_blocks_ordered(
    html: str,
    year: int,
    strength_mondays: dict[str, str],
) -> tuple[dict[str, ParsedWeek], dict[str, list[str]], list[ParsedDay]]:
    """Parse each week-block section in document order."""
    weeks: dict[str, ParsedWeek] = {}
    schedule: dict[str, list[str]] = {}
    unmapped: list[ParsedDay] = []

    title_re = re.compile(
        r'<div class="week-title">\s*(.*?)\s*<span class="week-dates">([^<]+)</span>'
        r'\s*<span class="week-phase[^"]*">([^<]+)</span>',
        re.DOTALL,
    )
    row_re = re.compile(r'<div class="day-row[^"]*">(.*?)</div>', re.DOTALL)
    label_re = re.compile(r'<span class="day-label">([^<]+)</span>')
    note_re = re.compile(
        r'<span class="day-note">(.*)</span>\s*<span class="run-cell',
        re.DOTALL,
    )
    run_re = re.compile(r'<span class="run-cell[^"]*">([^<]*)</span>')

    for chunk in _iter_week_block_chunks(html):
        tm = title_re.search(chunk)
        if not tm:
            continue
        title_raw = re.sub(r"<[^>]+>", " ", tm.group(1))
        title = " ".join(title_raw.split())
        dates_text = tm.group(2).strip()
        phase = tm.group(3).strip()

        try:
            week_start, week_end = _parse_week_dates(dates_text)
        except ValueError:
            continue

        key = _slug_week(title, dates_text)
        pw = ParsedWeek(key=key, label=f"{title} ({dates_text})", phase=phase)

        for rm in row_re.finditer(chunk):
            row = rm.group(1)
            lm = label_re.search(row)
            run_m = run_re.search(row)
            note_m = note_re.search(row)
            if not lm or not run_m:
                continue
            label = lm.group(1).strip()
            note = re.sub(r"<[^>]+>", " ", note_m.group(1)).strip() if note_m else ""
            run = run_m.group(1).strip()
            try:
                d = _parse_day_label(label, week_start, week_end, year)
            except ValueError:
                continue
            yyyymmdd = d.strftime("%Y%m%d")
            workout_keys, skip = _map_run_to_workouts(run, note, yyyymmdd, strength_mondays)
            pd = ParsedDay(yyyymmdd, label, run, note, workout_keys[0] if workout_keys else None, skip)
            if workout_keys:
                pw.days[yyyymmdd] = workout_keys
                schedule[yyyymmdd] = workout_keys
            else:
                pw.skipped.append(pd)
                if skip and skip.startswith("unmapped"):
                    unmapped.append(pd)

        if pw.days or pw.skipped:
            weeks[key] = pw

    return weeks, schedule, unmapped


def weeks_for_coros(plan: ParsedPlan | None = None) -> dict[str, dict]:
    """Format compatible with workout_sync.schedules.WEEKS."""
    p = plan or parse_plan_html()
    return {
        k: {"label": w.label, "days": dict(w.days)}
        for k, w in p.weeks.items()
    }


def load_weeks(html_path: Path | None = None) -> dict[str, dict]:
    """Return WEEKS dict from plan HTML (cached per call)."""
    return weeks_for_coros(parse_plan_html(html_path))
