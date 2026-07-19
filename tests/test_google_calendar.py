import json

from workout_sync.google_calendar import event_body, sync_google_calendar


class Request:
    def __init__(self, result=None):
        self.result = result or {}

    def execute(self):
        return self.result


class Events:
    def __init__(self, existing):
        self.existing = existing
        self.inserted = []
        self.updated = []
        self.deleted = []

    def list(self, **kwargs):
        return Request({"items": self.existing})

    def insert(self, **kwargs):
        self.inserted.append(kwargs)
        return Request()

    def update(self, **kwargs):
        self.updated.append(kwargs)
        return Request()

    def delete(self, **kwargs):
        self.deleted.append(kwargs)
        return Request()


class Service:
    def __init__(self, existing):
        self.resource = Events(existing)

    def events(self):
        return self.resource


def exported_event(date="2026-07-19", key="easy_3k"):
    return {
        "summary": "Easy 3K",
        "description": "Shakeout",
        "start": {"date": date, "endDate": "unused"},
        "end": {"date": date, "endDate": "2026-07-20"},
        "date": date,
        "workoutKey": key,
    }


def test_event_body_is_all_day_and_managed():
    body = event_body(exported_event(), plan_title="Rebuild")

    assert body["start"] == {"date": "2026-07-19"}
    assert body["end"] == {"date": "2026-07-20"}
    assert body["transparency"] == "transparent"
    assert body["extendedProperties"]["private"] == {
        "source": "coros-mcp",
        "syncKey": "2026-07-19:easy_3k",
        "workoutKey": "easy_3k",
    }


def test_sync_creates_updates_and_deletes_managed_events(tmp_path):
    desired_event = exported_event()
    desired_body = event_body(desired_event, plan_title="Rebuild")
    changed_existing = {
        **desired_body,
        "id": "update-me",
        "summary": "Old title",
    }
    stale_existing = {
        **desired_body,
        "id": "delete-me",
        "extendedProperties": {
            "private": {
                "source": "coros-mcp",
                "syncKey": "2026-06-01:old",
                "workoutKey": "old",
            }
        },
    }
    export = tmp_path / "calendar.json"
    export.write_text(
        json.dumps(
            {
                "title": "Rebuild",
                "googleCalendar": {"events": [desired_event, exported_event("2026-07-21", "easy_4k")]},
            }
        )
    )
    service = Service([changed_existing, stale_existing])

    result = sync_google_calendar(export_path=export, service=service)

    assert result.created == 1
    assert result.updated == 1
    assert result.deleted == 1
    assert len(service.resource.inserted) == 1
    assert service.resource.updated[0]["eventId"] == "update-me"
    assert service.resource.deleted[0]["eventId"] == "delete-me"


def test_dry_run_does_not_write(tmp_path):
    export = tmp_path / "calendar.json"
    export.write_text(
        json.dumps({"title": "Rebuild", "googleCalendar": {"events": [exported_event()]}})
    )
    service = Service([])

    result = sync_google_calendar(export_path=export, service=service, dry_run=True)

    assert result.created == 1
    assert service.resource.inserted == []
