from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.streak import compute_streak, parse_activity_timestamp


REPO_ROOT = Path(__file__).resolve().parents[2]
UTC_ZONE = ZoneInfo("UTC")
UNIT_LESSONS = {
    "u1": ("l01", "l02", "l03"),
    "u2": ("l04", "l05", "l06"),
    "u3": ("l07", "l08", "l09"),
    "u4": ("l10", "l11", "l12"),
}


def _at(day: int, hour: int = 12, minute: int = 0) -> datetime:
    return datetime(2026, 3, day, hour, minute, tzinfo=UTC)


def _streak(
    lessons: list[tuple[str, datetime]] = [],
    reports: list[datetime] = [],
    *,
    now: datetime,
    timezone: ZoneInfo = UTC_ZONE,
) -> dict[str, int | bool]:
    return compute_streak(lessons, reports, UNIT_LESSONS, timezone, now)


def _client(tmp_path: Path) -> TestClient:
    return TestClient(
        create_app(
            manifest_path=REPO_ROOT / "content" / "lesson_path.json",
            lessons_dir=REPO_ROOT / "content" / "lessons",
            database_path=tmp_path / "progress.db",
        )
    )


def test_empty_history_returns_zero_streak_and_endpoint_today_target(tmp_path: Path) -> None:
    assert _streak(now=_at(3)) == {
        "streak_days": 0,
        "active_today": False,
        "freezes": 0,
        "freezes_earned_total": 0,
    }

    with _client(tmp_path) as client:
        response = client.get("/users/maya/streak")

    assert response.status_code == 200
    assert response.json() == {
        "streak_days": 0,
        "active_today": False,
        "freezes": 0,
        "today": {
            "kind": "lesson",
            "lesson_id": "l01-first-hello",
            "title": "First hello",
            "unit_id": "u1",
        },
    }


def test_three_consecutive_local_activity_days_increment_streak() -> None:
    result = _streak(reports=[_at(1), _at(2), _at(3)], now=_at(3, 18))

    assert result["streak_days"] == 3
    assert result["active_today"] is True


def test_today_without_activity_preserves_yesterday_streak_without_freeze() -> None:
    result = _streak(reports=[_at(2)], now=_at(3, 18))

    assert result == {
        "streak_days": 1,
        "active_today": False,
        "freezes": 0,
        "freezes_earned_total": 0,
    }


def test_gap_uses_banked_freeze_but_resets_without_one() -> None:
    with_freeze = _streak(
        lessons=[("l01", _at(1)), ("l02", _at(2)), ("l03", _at(3))],
        reports=[_at(5)],
        now=_at(5, 18),
    )
    without_freeze = _streak(reports=[_at(1), _at(3)], now=_at(3, 18))

    assert with_freeze["streak_days"] == 4
    assert with_freeze["freezes"] == 0
    assert without_freeze["streak_days"] == 1
    assert without_freeze["freezes"] == 0


def test_completed_units_earn_freezes_with_a_balance_cap() -> None:
    lessons = [
        (lesson_id, _at(1))
        for lesson_ids in UNIT_LESSONS.values()
        for lesson_id in lesson_ids
    ]

    result = _streak(lessons, now=_at(1, 18))

    assert result["freezes_earned_total"] == 4
    assert result["freezes"] == 2


def test_timezone_boundary_and_dst_transition_use_user_local_days() -> None:
    previous_night_utc = datetime(2026, 3, 8, 4, 30, tzinfo=UTC)
    dst_morning_utc = datetime(2026, 3, 8, 6, 30, tzinfo=UTC)
    new_york = ZoneInfo("America/New_York")

    assert previous_night_utc.astimezone(new_york).date().isoformat() == "2026-03-07"
    assert dst_morning_utc.astimezone(new_york).date().isoformat() == "2026-03-08"
    assert previous_night_utc.astimezone(UTC_ZONE).date() == dst_morning_utc.astimezone(UTC_ZONE).date()

    new_york_result = _streak(
        reports=[previous_night_utc, dst_morning_utc],
        timezone=new_york,
        now=datetime(2026, 3, 8, 18, tzinfo=UTC),
    )
    utc_result = _streak(
        reports=[previous_night_utc, dst_morning_utc],
        now=datetime(2026, 3, 8, 18, tzinfo=UTC),
    )

    assert new_york_result["streak_days"] == 2
    assert utc_result["streak_days"] == 1


def test_mixed_timestamp_parsing_deduplicates_a_day_and_skips_malformed_values() -> None:
    completion = parse_activity_timestamp("2026-03-07 23:30:00")
    report = parse_activity_timestamp("2026-03-07T23:45:00+00:00")

    assert completion is not None
    assert report is not None
    assert parse_activity_timestamp("not a timestamp") is None
    result = _streak([("l01", completion)], [report], now=_at(7, 23))
    assert result["streak_days"] == 1
    assert result["active_today"] is True


def test_streak_endpoint_rejects_invalid_timezone_and_reports_all_complete(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        invalid = client.get("/users/maya/streak", params={"tz": "Mars/Olympus"})
        assert invalid.status_code == 422
        assert invalid.json() == {"detail": "invalid_timezone"}

        store = client.app.state.progress_store
        for lesson in client.app.state.curriculum.lessons:
            store.record_completion("maya", lesson["id"])
        complete = client.get("/users/maya/streak", params={"tz": "America/New_York"})

    assert complete.status_code == 200
    assert complete.json()["today"] == {
        "kind": "all_complete", "lesson_id": None, "title": None, "unit_id": None,
    }
