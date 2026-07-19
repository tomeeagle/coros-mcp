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
        if refresh:
            _refresh_week(week)
        data = build_week_review(week, refresh=refresh).to_dict()
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


def _refresh_week(week: str | None) -> None:
    """Pull activities + daily metrics for the week into cache."""
    from cache.store import init_db
    from cache.sync import fetch_activities_cached, fetch_daily_records_cached
    from workout_sync.auth import ensure_auth

    async def _run():
        auth = await ensure_auth()
        start, end = week_bounds(week)
        # pad a day each side
        s = _ymd(start - timedelta(days=1))
        e = _ymd(end + timedelta(days=1))
        init_db()
        await fetch_activities_cached(auth, s, e, size=100)
        with contextlib.suppress(Exception):
            await fetch_daily_records_cached(auth, s, e)

    asyncio.run(_run())


def main(host: str = "127.0.0.1", port: int = 5055) -> None:
    from workout_sync.auth import load_dotenv

    load_dotenv()
    app = create_app()
    print(f"Weekly coach API → http://{host}:{port}")
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
