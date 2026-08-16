"""Local Flask API for the weekly coach UI."""

from __future__ import annotations

import asyncio
import contextlib
from datetime import timedelta

from flask import Flask, jsonify, request

from workout_sync.weekly_coach import _ymd, apply_suggestions, build_week_review, week_bounds


def create_app() -> Flask:
    app = Flask(__name__)

    @app.after_request
    def cors(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        resp.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        return resp

    @app.route("/health")
    def health():
        from workout_sync.auth import auth_status_message

        return jsonify({"ok": True, "auth": auth_status_message()})

    @app.route("/review", methods=["GET", "OPTIONS"])
    def review():
        if request.method == "OPTIONS":
            return ("", 204)
        week = request.args.get("week")
        refresh = request.args.get("refresh", "0") in ("1", "true", "yes")
        refresh_warning = None
        if refresh:
            try:
                _refresh_range(week, weeks_back=1)
            except Exception as exc:
                # Fall back to cached data rather than failing the whole review.
                refresh_warning = f"Couldn't refresh from Coros ({exc}). Showing cached data."
                refresh = False
        data = build_week_review(week, refresh=refresh).to_dict()
        if refresh_warning:
            data["refreshWarning"] = refresh_warning
        return jsonify(data)

    @app.route("/trends", methods=["GET", "OPTIONS"])
    def trends():
        if request.method == "OPTIONS":
            return ("", 204)
        week = request.args.get("week")
        week_count = 12
        raw_count = request.args.get("weeks", "12")
        if raw_count.isdigit():
            week_count = max(4, min(20, int(raw_count)))
        refresh = request.args.get("refresh", "0") in ("1", "true", "yes")
        refresh_warning = None
        if refresh:
            try:
                _refresh_range(week, weeks_back=week_count)
            except Exception as exc:
                refresh_warning = f"Couldn't refresh from Coros ({exc}). Showing cached data."
        from cache.store import get_activities, get_daily_records, get_sleep_records, init_db
        from workout_sync.weekly_performance import build_coach_trends

        init_db()
        start, end = week_bounds(week)
        range_start = start - timedelta(days=7 * (week_count - 1))
        start_s, end_s = _ymd(range_start), _ymd(end)
        data = build_coach_trends(
            get_activities(start_s, end_s),
            get_daily_records(start_s, end_s),
            get_sleep_records(start_s, end_s),
            week=week,
            week_count=week_count,
        )
        if refresh_warning:
            data["refreshWarning"] = refresh_warning
        return jsonify(data)

    @app.route("/review/apply", methods=["POST", "OPTIONS"])
    def review_apply():
        if request.method == "OPTIONS":
            return ("", 204)
        body = request.get_json(force=True, silent=True) or {}
        suggestions = body.get("suggestions") or body.get("nextWeekSuggestions") or []
        if not suggestions:
            return jsonify({"error": "No suggestions provided"}), 400
        result = apply_suggestions(suggestions)
        return jsonify(result)

    return app


def _refresh_range(week: str | None, *, weeks_back: int = 1) -> None:
    """Pull activities, daily metrics, and sleep into cache."""
    from cache.store import init_db
    from cache.sync import fetch_activities_cached, fetch_daily_records_cached, fetch_sleep_cached
    from workout_sync.auth import ensure_auth

    async def _run():
        auth = await ensure_auth()
        start, end = week_bounds(week)
        s = _ymd(start - timedelta(days=7 * max(0, weeks_back - 1) + 1))
        e = _ymd(end + timedelta(days=1))
        init_db()
        await fetch_activities_cached(auth, s, e, size=100)
        with contextlib.suppress(Exception):
            await fetch_daily_records_cached(auth, s, e)
        with contextlib.suppress(Exception):
            await fetch_sleep_cached(auth, s, e)

    asyncio.run(_run())


def main(host: str = "127.0.0.1", port: int = 5055) -> None:
    from workout_sync.auth import load_dotenv

    load_dotenv()
    app = create_app()
    print(f"Weekly coach API → http://{host}:{port}")
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
