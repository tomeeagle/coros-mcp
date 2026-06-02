"""Tests for workout_sync.push_schedule deduplication."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from workout_sync import sync as sync_mod


@pytest.mark.asyncio
async def test_push_schedule_clears_each_day_before_push():
    auth = object()
    schedule = {"20260603": ["run_club_8k"], "20260604": ["easy_4k"]}
    clear_mock = AsyncMock(return_value=(0, []))
    push_mock = AsyncMock()

    with (
        patch.object(sync_mod.coros_api, "clear_scheduled_workouts", clear_mock),
        patch.object(sync_mod, "push_session", push_mock),
    ):
        success, errors, _ = await sync_mod.push_schedule(
            schedule, auth=auth, clear_each_day=True,
        )

    assert success == 2
    assert errors == 0
    assert clear_mock.await_count == 2
    clear_mock.assert_any_await(auth, "20260603", "20260603")
    clear_mock.assert_any_await(auth, "20260604", "20260604")
    assert push_mock.await_count == 2


@pytest.mark.asyncio
async def test_push_schedule_skips_per_day_clear_when_disabled():
    auth = object()
    schedule = {"20260603": ["run_club_8k"]}
    clear_mock = AsyncMock(return_value=(0, []))

    with (
        patch.object(sync_mod.coros_api, "clear_scheduled_workouts", clear_mock),
        patch.object(sync_mod, "push_session", AsyncMock()),
    ):
        await sync_mod.push_schedule(schedule, auth=auth, clear_each_day=False)

    clear_mock.assert_not_awaited()
