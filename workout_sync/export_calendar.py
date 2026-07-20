"""Export plan HTML to Google Calendar JSON."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path

from workout_sync.plan_html import (
    DEFAULT_PLAN_PATH,
    _iter_week_block_chunks,
    _parse_day_label,
    _parse_plan_year,
    _parse_week_dates,
    parse_plan_html,
)
from workout_sync.workouts import WORKOUTS

DEFAULT_EXPORT_PATH = DEFAULT_PLAN_PATH.parent / "plan_calendar_export.json"


def export_calendar_json(
    html_path: Path | None = None,
    out_path: Path | None = None,
) -> Path:
    plan_path = html_path or DEFAULT_PLAN_PATH
    dest = out_path or DEFAULT_EXPORT_PATH
    html = plan_path.read_text(encoding="utf-8")
    year = _parse_plan_year(html)
    plan = parse_plan_html(plan_path)

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
    weight_re = re.compile(r'<span class="weight-cell[^"]*">([^<]*)</span>')

    def iso(ymd: str) -> str:
        return datetime.strptime(ymd, "%Y%m%d").strftime("%Y-%m-%d")

    def gcal(ymd: str) -> dict:
        end = (datetime.strptime(ymd, "%Y%m%d").date() + timedelta(days=1)).isoformat()
        return {"date": iso(ymd), "endDate": end}

    def workout_detail(key: str) -> dict:
        w = WORKOUTS.get(key, {})
        out = {"key": key, "name": w.get("name"), "kind": w.get("kind", "run")}
        if w.get("distance_meters"):
            out["distance_km"] = w["distance_meters"] / 1000
        return out

    blocks: list[dict] = []
    events: list[dict] = []

    for chunk in _iter_week_block_chunks(html):
        tm = title_re.search(chunk)
        if not tm:
            continue
        wt = " ".join(re.sub(r"<[^>]+>", " ", tm.group(1)).split())
        dt, ph = tm.group(2).strip(), tm.group(3).strip()
        try:
            ws, we = _parse_week_dates(dt)
        except ValueError:
            continue
        wn = re.search(r"Week\s+(\d+)", wt, re.I)
        block: dict = {
            "title": wt,
            "dates": dt,
            "phase": ph,
            "weekNumber": int(wn.group(1)) if wn else None,
            "days": [],
        }
        for rm in row_re.finditer(chunk):
            row = rm.group(1)
            lm, rm2, nm, wm = (
                label_re.search(row),
                run_re.search(row),
                note_re.search(row),
                weight_re.search(row),
            )
            if not lm or not rm2:
                continue
            lb = lm.group(1).strip()
            no = re.sub(r"<[^>]+>", " ", nm.group(1)).strip() if nm else ""
            ru = rm2.group(1).strip()
            weg = wm.group(1).strip() if wm else ""
            try:
                dd = _parse_day_label(lb, ws, we, year)
            except ValueError:
                continue
            y = dd.strftime("%Y%m%d")
            keys = plan.schedule.get(y, [])
            block["days"].append(
                {
                    "date": iso(y),
                    "dayLabel": lb,
                    "note": no,
                    "runPlan": ru if ru not in ("—", "-", "") else None,
                    "foodWeight": weg or None,
                    "workouts": [workout_detail(k) for k in keys],
                    "rest": not keys
                    and (not ru or ru.lower().startswith("rest") or ru in ("—", "-")),
                }
            )
            for k in keys:
                w = WORKOUTS.get(k, {})
                summary = w.get("name", k)
                optional = re.search(r"optional\s+(BAC|PFTC)", no, re.I)
                if optional:
                    summary = f"{summary} · {optional.group(1).upper()} optional"
                events.append(
                    {
                        "summary": summary,
                        "description": "\n".join(
                            x
                            for x in [
                                no,
                                f"Food: {weg}" if weg else "",
                                f"Plan: {ru}" if ru not in ("—", "-") else "",
                            ]
                            if x
                        ),
                        "start": gcal(y),
                        "end": gcal(y),
                        "date": iso(y),
                        "dayLabel": lb,
                        "weekTitle": wt,
                        "workoutKey": k,
                        "category": w.get("kind", "run"),
                    }
                )
        if block["days"]:
            blocks.append(block)

    dates = sorted(plan.schedule.keys()) if plan.schedule else []
    block_start = (
        f"{dates[0][:4]}-{dates[0][4:6]}-{dates[0][6:]}" if dates else None
    )
    block_end = (
        f"{dates[-1][:4]}-{dates[-1][4:6]}-{dates[-1][6:]}" if dates else None
    )

    payload = {
        "title": "Tom's Plan — 8-week rebuild",
        "blockStart": block_start or "2026-07-19",
        "blockEnd": block_end or "2026-09-12",
        "timezone": "Europe/London",
        "structure": (
            "Rebuild after layoff · Mon rest (optional Easy 3K) · Tue easy (BAC optional) · "
            "Wed easy/PFTC optional · Thu strength · Fri easy/progression · Sat long · no races"
        ),
        "weeks": blocks,
        "googleCalendar": {
            "hint": (
                "All-day events; set your own run times. "
                "Mon rest · Thu strength. BAC Tue + PFTC Wed optional — calendar shows the easy default."
            ),
            "events": sorted(events, key=lambda e: e["date"]),
        },
    }
    dest.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return dest
