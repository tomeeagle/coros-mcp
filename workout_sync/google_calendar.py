"""Direct Google Calendar sync for exported training-plan events."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from workout_sync.export_calendar import DEFAULT_EXPORT_PATH, export_calendar_json

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
SOURCE = "coros-mcp"
CONFIG_DIR = Path.home() / ".config" / "coros-mcp"
DEFAULT_CLIENT_SECRET_PATH = CONFIG_DIR / "google-calendar-client.json"
DEFAULT_TOKEN_PATH = CONFIG_DIR / "google-calendar-token.json"


@dataclass
class SyncResult:
    created: int = 0
    updated: int = 0
    deleted: int = 0
    unchanged: int = 0


def _client_secret_path() -> Path:
    return Path(
        os.environ.get("GOOGLE_CALENDAR_CLIENT_SECRET", DEFAULT_CLIENT_SECRET_PATH)
    ).expanduser()


def _token_path() -> Path:
    return Path(
        os.environ.get("GOOGLE_CALENDAR_TOKEN", DEFAULT_TOKEN_PATH)
    ).expanduser()


def _calendar_id() -> str:
    return os.environ.get("GOOGLE_CALENDAR_ID", "primary")


def authenticate_google_calendar(*, force: bool = False) -> Path:
    """Run installed-app OAuth and persist the refresh token locally."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise RuntimeError(
            "Google Calendar dependencies are missing. "
            "Install with: pip install -e '.[calendar]'"
        ) from exc

    client_path = _client_secret_path()
    token_path = _token_path()
    if not client_path.is_file():
        raise FileNotFoundError(
            f"Google OAuth client file not found: {client_path}\n"
            "Create a Desktop app OAuth client in Google Cloud, download its JSON, "
            f"and save it there (or set GOOGLE_CALENDAR_CLIENT_SECRET)."
        )

    credentials = None
    if token_path.is_file() and not force:
        credentials = Credentials.from_authorized_user_file(token_path, SCOPES)
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    if force or not credentials or not credentials.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(client_path), SCOPES)
        credentials = flow.run_local_server(port=0, open_browser=True)

    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(credentials.to_json(), encoding="utf-8")
    token_path.chmod(0o600)
    return token_path


def _credentials() -> Any:
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
    except ImportError as exc:
        raise RuntimeError(
            "Google Calendar dependencies are missing. "
            "Install with: pip install -e '.[calendar]'"
        ) from exc

    token_path = _token_path()
    if not token_path.is_file():
        raise FileNotFoundError(
            f"Google Calendar is not authenticated. Run: coros-mcp calendar-auth\n"
            f"Expected token: {token_path}"
        )
    credentials = Credentials.from_authorized_user_file(token_path, SCOPES)
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        token_path.write_text(credentials.to_json(), encoding="utf-8")
        token_path.chmod(0o600)
    if not credentials.valid:
        raise RuntimeError("Google Calendar credentials are invalid. Run: coros-mcp calendar-auth --force")
    return credentials


def build_calendar_service() -> Any:
    """Create an authenticated Calendar API service."""
    try:
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError(
            "Google Calendar dependencies are missing. "
            "Install with: pip install -e '.[calendar]'"
        ) from exc
    return build("calendar", "v3", credentials=_credentials(), cache_discovery=False)


def _sync_key(event: dict[str, Any]) -> str:
    return f"{event['date']}:{event['workoutKey']}"


def event_body(event: dict[str, Any], *, plan_title: str) -> dict[str, Any]:
    """Convert one exported event to a Google Calendar all-day event."""
    sync_key = _sync_key(event)
    description = event.get("description", "").strip()
    footer = f"Managed by {SOURCE}\nPlan: {plan_title}"
    return {
        "summary": event["summary"],
        "description": f"{description}\n\n{footer}".strip(),
        "start": {"date": event["start"]["date"]},
        "end": {"date": event["end"]["endDate"]},
        "transparency": "transparent",
        "extendedProperties": {
            "private": {
                "source": SOURCE,
                "syncKey": sync_key,
                "workoutKey": event["workoutKey"],
            }
        },
    }


def _comparable(event: dict[str, Any]) -> dict[str, Any]:
    keys = ("summary", "description", "start", "end", "transparency", "extendedProperties")
    return {key: event.get(key) for key in keys}


def _list_managed_events(service: Any, calendar_id: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    page_token = None
    while True:
        response = (
            service.events()
            .list(
                calendarId=calendar_id,
                privateExtendedProperty=f"source={SOURCE}",
                singleEvents=True,
                maxResults=2500,
                pageToken=page_token,
            )
            .execute()
        )
        events.extend(response.get("items", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            return events


def sync_google_calendar(
    *,
    export_path: Path | None = None,
    calendar_id: str | None = None,
    dry_run: bool = False,
    service: Any | None = None,
) -> SyncResult:
    """Reconcile project-managed Google Calendar events with the plan export."""
    path = export_path or DEFAULT_EXPORT_PATH
    if export_path is None:
        path = export_calendar_json()
    payload = json.loads(path.read_text(encoding="utf-8"))
    desired_events = payload.get("googleCalendar", {}).get("events", [])
    desired = {
        _sync_key(event): event_body(event, plan_title=payload["title"])
        for event in desired_events
    }

    service = service or build_calendar_service()
    selected_calendar = calendar_id or _calendar_id()
    existing_events = _list_managed_events(service, selected_calendar)
    existing = {
        event.get("extendedProperties", {}).get("private", {}).get("syncKey"): event
        for event in existing_events
    }
    existing.pop(None, None)

    result = SyncResult()
    for sync_key, body in desired.items():
        current = existing.get(sync_key)
        if current is None:
            result.created += 1
            if not dry_run:
                service.events().insert(calendarId=selected_calendar, body=body).execute()
        elif _comparable(current) != _comparable(body):
            result.updated += 1
            if not dry_run:
                service.events().update(
                    calendarId=selected_calendar,
                    eventId=current["id"],
                    body=body,
                ).execute()
        else:
            result.unchanged += 1

    for sync_key, current in existing.items():
        if sync_key not in desired:
            result.deleted += 1
            if not dry_run:
                service.events().delete(
                    calendarId=selected_calendar,
                    eventId=current["id"],
                ).execute()
    return result
