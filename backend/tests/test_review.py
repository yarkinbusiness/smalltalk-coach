from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from backend.app.content import load_curriculum
from backend.app.main import _review_priority_dimension, create_app
from backend.app.review import build_review_queue
from backend.app.streak import compute_streak


REPO_ROOT = Path(__file__).resolve().parents[2]
UTC_ZONE = ZoneInfo("UTC")
UNIT_LESSONS = {"u1": ("l01", "l02", "l03")}


def _at(month: int, day: int, hour: int = 12) -> datetime:
    return datetime(2026, month, day, hour, tzinfo=UTC)


def _curriculum():
    return load_curriculum(REPO_ROOT / "content" / "lesson_path.json", REPO_ROOT / "content" / "lessons")


def _queue(
    completions: list[tuple[str, datetime]],
    reviews: list[tuple[str, datetime]],
    *,
    priority: str | None = None,
    timezone: ZoneInfo = UTC_ZONE,
    now: datetime,
) -> list[dict[str, str | int]]:
    return build_review_queue(completions, reviews, _curriculum(), priority, timezone, now)


def _client(tmp_path: Path) -> TestClient:
    return TestClient(
        create_app(
            manifest_path=REPO_ROOT / "content" / "lesson_path.json",
            lessons_dir=REPO_ROOT / "content" / "lessons",
            database_path=tmp_path / "progress.db",
        )
    )


def _correct_answers(lesson: dict[str, object]) -> dict[str, int]:
    return {
        str(index): part["correct_option_index"]
        for index, part in enumerate(lesson["completion_check"]["parts"])
        if part["kind"] == "choice"
    }


def _set_completion_dates(database_path: Path, value: str) -> None:
    with sqlite3.connect(database_path) as connection:
        connection.execute("UPDATE lesson_completions SET completed_at = ?", (value,))


def test_review_ladder_advances_from_each_review_and_omits_upcoming_lessons() -> None:
    completion = [("l01-first-hello", _at(3, 1))]

    assert _queue(completion, [], now=_at(3, 3)) == []
    assert _queue(completion, [], now=_at(3, 4))[0]["days_overdue"] == 0

    first_review = [("l01-first-hello", _at(3, 4))]
    assert _queue(completion, first_review, now=_at(3, 10)) == []
    assert _queue(completion, first_review, now=_at(3, 11))[0]["days_overdue"] == 0

    second_review = [*first_review, ("l01-first-hello", _at(3, 11))]
    assert _queue(completion, second_review, now=_at(3, 31)) == []
    assert _queue(completion, second_review, now=_at(4, 1))[0]["days_overdue"] == 0

    third_review = [*second_review, ("l01-first-hello", _at(4, 1))]
    assert _queue(completion, third_review, now=_at(4, 21)) == []
    assert _queue(completion, third_review, now=_at(4, 22))[0]["days_overdue"] == 0


def test_review_queue_respects_user_local_dates_at_a_timezone_boundary() -> None:
    completion = [("l01-first-hello", datetime(2026, 3, 8, 4, 30, tzinfo=UTC))]
    now = datetime(2026, 3, 10, 18, tzinfo=UTC)

    assert _queue(completion, [], timezone=ZoneInfo("America/New_York"), now=now)
    assert _queue(completion, [], timezone=UTC_ZONE, now=now) == []


def test_priority_uses_recurring_then_highest_flagged_dimension_and_overdue_order() -> None:
    completions = [
        ("l01-first-hello", _at(3, 1)),
        ("l03-easy-first-question", _at(3, 2)),
        ("l04-answer-and-return", _at(3, 3)),
    ]
    due = _queue(completions, [], priority="curiosity", now=_at(3, 10))
    assert [item["lesson_id"] for item in due] == [
        "l03-easy-first-question", "l04-answer-and-return", "l01-first-hello",
    ]
    assert [item["dimension"] for item in due[:2]] == ["curiosity", "curiosity"]

    profile = {
        "recurring_weakness": None,
        "dimensions": {
            "warmth": {"flagged_count": 1},
            "curiosity": {"flagged_count": 3},
            "reciprocity": {"flagged_count": 2},
        },
    }
    assert _review_priority_dimension(profile) == "curiosity"
    assert _review_priority_dimension({
        **profile,
        "recurring_weakness": {"dimension": "warmth", "flagged_recent": 3, "window": 3},
    }) == "warmth"


def test_review_post_shares_grading_and_only_persists_passing_completed_lessons(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        lesson = client.get("/lessons/l01-first-hello", params={"user_id": "maya"}).json()
        answers = _correct_answers(lesson)
        client.post("/lessons/l01-first-hello/complete", json={"user_id": "maya", "answers": answers})

        passed = client.post("/lessons/l01-first-hello/review", json={"user_id": "maya", "answers": answers})
        assert passed.status_code == 200
        assert passed.json() == {"completed": True, "unlocked_next": "l02-use-the-setting"}
        assert len(client.app.state.progress_store.review_timestamps("maya")) == 1

        failed = client.post("/lessons/l01-first-hello/review", json={"user_id": "maya", "answers": {"0": 1}})
        assert failed.json()["completed"] is False
        assert len(client.app.state.progress_store.review_timestamps("maya")) == 1

        not_completed = client.post("/lessons/l02-use-the-setting/review", json={"user_id": "maya", "answers": {}})
        assert not_completed.status_code == 409
        assert not_completed.json() == {"detail": "not_completed"}
        unknown = client.post("/lessons/nope/review", json={"user_id": "maya", "answers": {}})
        assert unknown.status_code == 404
        assert unknown.json() == {"detail": "lesson_not_found"}


def test_reviews_extend_streak_without_earning_freezes() -> None:
    streak = compute_streak(
        [],
        [_at(3, 1)],
        UNIT_LESSONS,
        UTC_ZONE,
        _at(3, 2),
        [_at(3, 2)],
    )

    assert streak == {
        "streak_days": 2,
        "active_today": True,
        "freezes": 0,
        "freezes_earned_total": 0,
    }


def test_streak_today_uses_due_review_only_after_the_path_is_complete(tmp_path: Path) -> None:
    database_path = tmp_path / "progress.db"
    with _client(tmp_path) as client:
        store = client.app.state.progress_store
        for lesson in client.app.state.curriculum.lessons:
            store.record_completion("maya", lesson["id"])
        _set_completion_dates(database_path, "2020-01-01 00:00:00")

        due_review = client.get("/users/maya/streak")
        assert due_review.json()["today"] == {
            "kind": "review",
            "lesson_id": "l01-first-hello",
            "title": "First hello",
            "unit_id": "u1",
        }

        _set_completion_dates(database_path, "2099-01-01 00:00:00")
        all_complete = client.get("/users/maya/streak")
        assert all_complete.json()["today"] == {
            "kind": "all_complete", "lesson_id": None, "title": None, "unit_id": None,
        }

    with _client(tmp_path / "unfinished") as client:
        unchanged = client.get("/users/maya/streak")
    assert unchanged.json()["today"]["kind"] == "lesson"


def test_review_queue_endpoint_validates_timezone_and_returns_due_items(tmp_path: Path) -> None:
    database_path = tmp_path / "progress.db"
    with _client(tmp_path) as client:
        store = client.app.state.progress_store
        store.record_completion("maya", "l01-first-hello")
        _set_completion_dates(database_path, "2020-01-01 00:00:00")

        invalid = client.get("/users/maya/review-queue", params={"tz": "Mars/Olympus"})
        assert invalid.status_code == 422
        assert invalid.json() == {"detail": "invalid_timezone"}
        due = client.get("/users/maya/review-queue", params={"tz": "UTC"})

    assert due.json()["due"] == [{
        "lesson_id": "l01-first-hello",
        "title": "First hello",
        "unit_id": "u1",
        "days_overdue": due.json()["due"][0]["days_overdue"],
        "dimension": "warmth",
    }]


def test_l02_loader_accepts_varied_correct_option_indices() -> None:
    lesson = _curriculum().content["l02-use-the-setting"]
    indices = {lesson["exercise"]["correct_option_index"]}
    indices.update(
        part["correct_option_index"]
        for part in lesson["completion_check"]["parts"]
        if part["kind"] == "choice"
    )
    assert len(indices) >= 2
