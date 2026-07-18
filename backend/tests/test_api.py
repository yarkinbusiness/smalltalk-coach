from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import create_app


REPO_ROOT = Path(__file__).resolve().parents[2]


def _client(tmp_path: Path) -> TestClient:
    return TestClient(
        create_app(
            manifest_path=REPO_ROOT / "content" / "lesson_path.json",
            lessons_dir=REPO_ROOT / "content" / "lessons",
            database_path=tmp_path / "progress.db",
        )
    )


def _states(payload: dict[str, object]) -> dict[str, str]:
    units = payload["units"]
    return {
        lesson["id"]: lesson["state"]
        for unit in units
        for lesson in unit["lessons"]
    }


def test_health_and_initial_curriculum(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        assert client.get("/health").json() == {"status": "ok", "lessons_loaded": 1}
        response = client.get("/curriculum", params={"user_id": "maya"})

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["units"]) == 4
    states = _states(payload)
    assert states["l01-first-hello"] == "unlocked"
    assert all(states[f"l{number:02d}-" + suffix] == "locked" for number, suffix in [
        (2, "use-the-setting"), (3, "easy-first-question"), (4, "answer-and-return"),
        (5, "show-you-heard"), (6, "follow-the-thread"), (7, "share-and-make-space"),
        (8, "handle-the-pause"), (9, "read-the-room"), (10, "build-on-common-ground"),
        (11, "end-warmly"), (12, "make-continuity-easy"),
    ])
    lessons = [lesson for unit in payload["units"] for lesson in unit["lessons"]]
    assert [lesson["id"] for lesson in lessons if lesson["content_available"]] == ["l01-first-hello"]


def test_lesson_error_distinctions_and_locked_completion(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        assert client.get("/lessons/l02-use-the-setting", params={"user_id": "maya"}).status_code == 423
        assert client.get("/lessons/nope", params={"user_id": "maya"}).status_code == 404
        assert client.post(
            "/lessons/l02-use-the-setting/complete",
            json={"user_id": "maya", "answers": {}},
        ).status_code == 423

        complete = client.post(
            "/lessons/l01-first-hello/complete",
            json={"user_id": "maya", "answers": {"0": 0}},
        )
        assert complete.json() == {"completed": True, "unlocked_next": "l02-use-the-setting"}
        pending = client.get("/lessons/l02-use-the-setting", params={"user_id": "maya"})

    assert pending.status_code == 404
    assert pending.json()["detail"] == "content_pending"


def test_completion_unlocks_l02_and_is_idempotent(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        correct = {"user_id": "maya", "answers": {"0": 0}}
        first = client.post("/lessons/l01-first-hello/complete", json=correct)
        second = client.post("/lessons/l01-first-hello/complete", json=correct)
        curriculum = client.get("/curriculum", params={"user_id": "maya"}).json()
        review = client.get("/lessons/l01-first-hello", params={"user_id": "maya"})

    assert first.json() == second.json() == {
        "completed": True,
        "unlocked_next": "l02-use-the-setting",
    }
    states = _states(curriculum)
    assert states["l01-first-hello"] == "completed"
    assert states["l02-use-the-setting"] == "unlocked"
    assert review.status_code == 200
    assert review.json()["id"] == "l01-first-hello"


def test_wrong_answer_returns_feedback_without_unlocking(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        wrong = client.post(
            "/lessons/l01-first-hello/complete",
            json={"user_id": "maya", "answers": {"0": 1}},
        )
        curriculum = client.get("/curriculum", params={"user_id": "maya"}).json()

    assert wrong.json()["completed"] is False
    assert wrong.json()["feedback"]["0"]
    states = _states(curriculum)
    assert states["l01-first-hello"] == "unlocked"
    assert states["l02-use-the-setting"] == "locked"
