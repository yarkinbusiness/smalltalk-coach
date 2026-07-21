from __future__ import annotations

from pathlib import Path
from shutil import copyfile

from fastapi.testclient import TestClient

from backend.app.main import create_app


REPO_ROOT = Path(__file__).resolve().parents[2]
LESSONS_DIR = REPO_ROOT / "content" / "lessons"


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


def _correct_choice_answers(lesson: dict[str, object]) -> dict[str, int]:
    return {
        str(index): part["correct_option_index"]
        for index, part in enumerate(lesson["completion_check"]["parts"])
        if part["kind"] == "choice"
    }


def test_health_and_initial_curriculum(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        assert client.get("/health").json() == {
            "status": "ok", "lessons_loaded": 12, "coaching_enabled": False,
            "auth_enabled": False,
        }
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
    assert [lesson["id"] for lesson in lessons if lesson["content_available"]] == [
        "l01-first-hello",
        "l02-use-the-setting",
        "l03-easy-first-question",
        "l04-answer-and-return",
        "l05-show-you-heard",
        "l06-follow-the-thread",
        "l07-share-and-make-space",
        "l08-handle-the-pause",
        "l09-read-the-room",
        "l10-build-on-common-ground",
        "l11-end-warmly",
        "l12-make-continuity-easy",
    ]


def test_lesson_error_distinctions_and_locked_completion(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        assert client.get("/lessons/l02-use-the-setting", params={"user_id": "maya"}).status_code == 423
        assert client.get("/lessons/nope", params={"user_id": "maya"}).status_code == 404
        assert client.post(
            "/lessons/l02-use-the-setting/complete",
            json={"user_id": "maya", "answers": {}},
        ).status_code == 423

        first_lesson = client.get("/lessons/l01-first-hello", params={"user_id": "maya"})
        assert first_lesson.status_code == 200
        complete = client.post(
            "/lessons/l01-first-hello/complete",
            json={"user_id": "maya", "answers": _correct_choice_answers(first_lesson.json())},
        )
        assert complete.json() == {"completed": True, "unlocked_next": "l02-use-the-setting"}
        lesson_ids = (
            "l02-use-the-setting",
            "l03-easy-first-question",
            "l04-answer-and-return",
            "l05-show-you-heard",
            "l06-follow-the-thread",
            "l07-share-and-make-space",
            "l08-handle-the-pause",
            "l09-read-the-room",
            "l10-build-on-common-ground",
            "l11-end-warmly",
            "l12-make-continuity-easy",
        )
        for lesson_id in lesson_ids:
            lesson = client.get(f"/lessons/{lesson_id}", params={"user_id": "maya"})
            assert lesson.status_code == 200
            completion = client.post(
                f"/lessons/{lesson_id}/complete",
                json={"user_id": "maya", "answers": _correct_choice_answers(lesson.json())},
            )
            if lesson_id == "l12-make-continuity-easy":
                assert completion.json() == {"completed": True, "unlocked_next": None}
            else:
                assert completion.json()["completed"] is True
        curriculum = client.get("/curriculum", params={"user_id": "maya"}).json()

    states = _states(curriculum)
    assert len(states) == 12
    assert all(state == "completed" for state in states.values())
    assert "unlocked" not in states.values()


def test_content_pending_when_next_unlocked_lesson_is_not_authored(tmp_path: Path) -> None:
    lessons_dir = tmp_path / "lessons"
    lessons_dir.mkdir()
    copyfile(LESSONS_DIR / "l01-first-hello.json", lessons_dir / "l01-first-hello.json")
    app = create_app(
        manifest_path=REPO_ROOT / "content" / "lesson_path.json",
        lessons_dir=lessons_dir,
        database_path=tmp_path / "progress.db",
    )

    with TestClient(app) as client:
        first_lesson = client.get("/lessons/l01-first-hello", params={"user_id": "maya"})
        complete = client.post(
            "/lessons/l01-first-hello/complete",
            json={"user_id": "maya", "answers": _correct_choice_answers(first_lesson.json())},
        )
        pending = client.get("/lessons/l02-use-the-setting", params={"user_id": "maya"})

    assert complete.json() == {"completed": True, "unlocked_next": "l02-use-the-setting"}
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
