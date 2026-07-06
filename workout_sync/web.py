"""Web UI: edit training_plan.html, click Sync to replace COROS calendar."""

from __future__ import annotations

import asyncio
from html import escape
from workout_sync import schedules as sched_mod
from workout_sync.auth import auth_status_message, load_dotenv
from workout_sync.plan_html import DEFAULT_PLAN_PATH
import coros_api
from workout_sync.sync import describe_session, full_resync, resolve_schedule


def _page(body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>COROS Workout Sync</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 44rem; margin: 2rem auto; padding: 0 1rem; }}
    h1 {{ font-size: 1.4rem; }}
    .card {{ border: 1px solid #ddd; border-radius: 8px; padding: 1.25rem; margin: 1rem 0; }}
    .primary {{
      display: block; width: 100%; padding: 1rem; font-size: 1.1rem; font-weight: 600;
      background: #1A6B3C; color: white; border: none; border-radius: 8px; cursor: pointer;
    }}
    .primary:hover {{ background: #145a32; }}
    .muted {{ font-size: 0.85rem; color: #666; }}
    .ok {{ color: #0a0; }}
    .err {{ color: #a00; }}
    ul {{ font-size: 0.9rem; line-height: 1.6; max-height: 20rem; overflow-y: auto; }}
    code {{ background: #f0f0f0; padding: 2px 6px; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>🏃 COROS Workout Sync</h1>
  {body}
</body>
</html>"""


def _index_html() -> str:
    load_dotenv()
    sched_mod.reload_schedules()
    auth_line = escape(auth_status_message())
    plan_path = DEFAULT_PLAN_PATH
    schedule = resolve_schedule(upcoming_only=True)
    total = sum(len(k) for k in sched_mod.SCHEDULE.values())
    upcoming = sum(len(k) for k in schedule.values())

    preview = "".join(
        f"<li>{escape(describe_session(d, k))}</li>"
        for d, k in list(schedule.items())[:12]
    )
    more = ""
    if len(schedule) > 12:
        more = f"<li class='muted'>… and {len(schedule) - 12} more</li>"

    return _page(
        f"""
  <p class="muted">Auth: {auth_line}</p>

  <div class="card">
    <h2 style="margin:0 0 0.5rem;font-size:1.1rem">1. Edit your plan</h2>
    <p class="muted" style="margin:0">
      Open <code>{escape(plan_path.name)}</code> in this repo, save your changes, then sync.
    </p>
  </div>

  <div class="card" style="background:#f7f9fc;border-color:#c5d4e8">
    <h2 style="margin:0 0 0.5rem;font-size:1.1rem">Where workouts appear in COROS</h2>
    <p class="muted" style="margin:0;line-height:1.5">
      Sync puts sessions on your <strong>training calendar</strong> (Progress tab in the app),
      <em>not</em> as a new plan in <strong>Training Plan Library</strong>.
      That library is only for separate multi-week templates (Marathon plan, TrainingPeaks, etc.).
      On the watch: open <strong>Run</strong> → accept today&apos;s scheduled workout when prompted.
    </p>
  </div>

  <div class="card">
    <h2 style="margin:0 0 0.5rem;font-size:1.1rem">2. Sync to COROS</h2>
    <p class="muted">
      Clears all calendar workouts in the plan date range, then pushes
      <strong>{upcoming}</strong> upcoming session(s) ({total} total in plan).
    </p>
    <form method="post" action="/sync" style="margin-top:1rem">
      <label class="muted" style="display:block;margin-bottom:0.75rem">
        <input type="checkbox" name="upcoming_only" value="1" checked>
        Upcoming sessions only (from today)
      </label>
      <button type="submit" class="primary">Sync plan to COROS</button>
    </form>
    <p class="muted" style="margin:1rem 0 0">
      Set <code>COROS_EMAIL</code> and <code>COROS_PASSWORD</code> in <code>.env</code>
      (see <code>.env.example</code>).
    </p>
  </div>

  <div class="card">
    <h3 style="margin:0 0 0.5rem;font-size:1rem">Preview (upcoming)</h3>
    <ul>{preview}{more}</ul>
  </div>
"""
    )


def create_app():
    try:
        from flask import Flask, request
    except ImportError as exc:
        raise ImportError("pip install -e '.[sync]'") from exc

    app = Flask(__name__)

    @app.get("/")
    def index():
        return _index_html()

    @app.post("/sync")
    def sync():
        upcoming_only = request.form.get("upcoming_only") == "1"

        try:

            async def _run():
                return await full_resync(upcoming_only=upcoming_only)

            result = asyncio.run(_run())
        except Exception as exc:
            return _page(
                f'<p class="err">Sync failed: {escape(str(exc))}</p>'
                f'<p><a href="/">Back</a></p>'
            ), 500

        lines = "".join(
            f"<li class='{'ok' if not l.startswith('Failed') else 'err'}'>{escape(l)}</li>"
            for l in result["messages"][-40:]
        )
        summary = (
            f"<p class='ok'>Removed <strong>{result['removed']}</strong> calendar "
            f"workout(s), pushed <strong>{result['pushed']}</strong>."
            f"{' (' + str(result['push_errors']) + ' errors)' if result['push_errors'] else ''}</p>"
        )
        cal = result.get("calendar_plan") or {}
        cal_line = ""
        if cal.get("name"):
            cal_line = (
                f"<p class='muted'>COROS calendar plan: <strong>{escape(cal['name'])}</strong> "
                f"— look under <strong>Progress</strong>, not Training Plan Library.</p>"
            )
        return _page(
            f"{summary}"
            f"{cal_line}"
            f"<p class='muted'>Cleared range: {escape(result['clear_range'])}</p>"
            f"<ul>{lines}</ul>"
            f"<p class='muted'>{escape(coros_api.format_calendar_vs_library_help())}</p>"
            f"<p><a href='/'>Back</a></p>"
        )

    return app


def run_server(host: str = "127.0.0.1", port: int = 5055) -> None:
    load_dotenv()
    app = create_app()
    print(f"\nPlan file: {DEFAULT_PLAN_PATH}")
    print(f"Auth: {auth_status_message()}")
    print(f"\nOpen http://{host}:{port}/\n")
    app.run(host=host, port=port, debug=False)
