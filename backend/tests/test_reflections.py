from __future__ import annotations

from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient

from backend.app.main import create_app


REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "content" / "lesson_path.json"
LESSONS_DIR = REPO_ROOT / "content" / "lessons"


def _client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(
        manifest_path=MANIFEST_PATH,
        lessons_dir=LESSONS_DIR,
        database_path=tmp_path / "progress.db",
    ))


def _save_report(client: TestClient, report_id: str, user_id: str) -> None:
    client.app.state.progress_store.save_coaching_report(
        report_id=report_id,
        user_id=user_id,
        transcript={"source_kind": "text"},
        diagnosis={},
        weakest_dimension="reciprocity",
        lesson_id="l04-answer-and-return",
        recommendation_kind="new",
        practice_action="Practice.",
    )


def _save_reflection(
    client: TestClient,
    reflection_id: str,
    outcome: str,
    created_at: str,
) -> None:
    store = client.app.state.progress_store
    store.save_reflection(
        reflection_id=reflection_id,
        user_id="maya",
        subject_kind="lesson",
        subject_id="l01-first-hello",
        outcome=outcome,
        note="private reflection",
    )
    with store._connect() as connection:
        connection.execute(
            "UPDATE reflections SET created_at = ? WHERE id = ?",
            (created_at, reflection_id),
        )
        connection.commit()


def test_lesson_reflection_round_trip_is_newest_first_and_preserves_note(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        first = client.post("/users/maya/reflections", json={
            "subject_kind": "lesson",
            "subject_id": "l01-first-hello",
            "outcome": "went_well",
            "note": "Gülümsemek yardımcı oldu 😊",
        })
        second = client.post("/users/maya/reflections", json={
            "subject_kind": "lesson",
            "subject_id": "l02-use-the-setting",
            "outcome": "partly",
            "note": "",
        })
        response = client.get("/users/maya/reflections")

    assert first.status_code == 201
    assert second.status_code == 201
    assert UUID(first.json()["id"])
    assert first.json()["created_at"]
    assert response.status_code == 200
    reflections = response.json()["reflections"]
    assert [reflection["id"] for reflection in reflections] == [
        second.json()["id"], first.json()["id"],
    ]
    assert reflections[1]["note"] == "Gülümsemek yardımcı oldu 😊"


def test_report_reflection_requires_an_owned_existing_report(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        _save_report(client, "maya-report", "maya")
        _save_report(client, "other-report", "other")
        owned = client.post("/users/maya/reflections", json={
            "subject_kind": "report",
            "subject_id": "maya-report",
            "outcome": "went_well",
        })
        other_user = client.post("/users/maya/reflections", json={
            "subject_kind": "report",
            "subject_id": "other-report",
            "outcome": "went_well",
        })
        unknown_report = client.post("/users/maya/reflections", json={
            "subject_kind": "report",
            "subject_id": "missing-report",
            "outcome": "went_well",
        })
        unknown_lesson = client.post("/users/maya/reflections", json={
            "subject_kind": "lesson",
            "subject_id": "missing-lesson",
            "outcome": "went_well",
        })

    assert owned.status_code == 201
    assert other_user.json() == {"detail": "unknown_subject"}
    assert unknown_report.json() == {"detail": "unknown_subject"}
    assert unknown_lesson.json() == {"detail": "unknown_subject"}
    assert other_user.status_code == unknown_report.status_code == unknown_lesson.status_code == 404


def test_reflection_validation_uses_stable_codes_and_defaults_note(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        invalid_kind = client.post("/users/maya/reflections", json={
            "subject_kind": "conversation",
            "subject_id": "l01-first-hello",
            "outcome": "went_well",
        })
        invalid_outcome = client.post("/users/maya/reflections", json={
            "subject_kind": "lesson",
            "subject_id": "l01-first-hello",
            "outcome": "great",
        })
        too_long = client.post("/users/maya/reflections", json={
            "subject_kind": "lesson",
            "subject_id": "l01-first-hello",
            "outcome": "went_well",
            "note": "x" * 501,
        })
        non_string_note = client.post("/users/maya/reflections", json={
            "subject_kind": "lesson",
            "subject_id": "l01-first-hello",
            "outcome": "went_well",
            "note": 12,
        })
        default_note = client.post("/users/maya/reflections", json={
            "subject_kind": "lesson",
            "subject_id": "l01-first-hello",
            "outcome": "avoided",
        })
        reflections = client.get("/users/maya/reflections")

    assert invalid_kind.status_code == 422
    assert invalid_kind.json() == {"detail": "invalid_subject_kind"}
    assert invalid_outcome.status_code == 422
    assert invalid_outcome.json() == {"detail": "invalid_outcome"}
    assert too_long.status_code == non_string_note.status_code == 422
    assert too_long.json() == non_string_note.json() == {"detail": "invalid_note"}
    assert default_note.status_code == 201
    assert reflections.json()["reflections"] == [{
        "id": default_note.json()["id"],
        "subject_kind": "lesson",
        "subject_id": "l01-first-hello",
        "outcome": "avoided",
        "note": "",
        "created_at": default_note.json()["created_at"],
    }]


def test_profile_reflection_summary_is_private_capped_and_newest_first(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        outcomes = ["went_well", "partly", "avoided", "went_well", "partly", "avoided"]
        for index, outcome in enumerate(outcomes, start=1):
            _save_reflection(
                client,
                f"reflection-{index}",
                outcome,
                f"2026-03-{index:02}T12:00:00+00:00",
            )
        profile = client.get("/users/maya/profile")

    assert profile.status_code == 200
    reflections = profile.json()["reflections"]
    assert reflections["counts"] == {"went_well": 2, "partly": 2, "avoided": 2}
    assert [item["subject_id"] for item in reflections["recent"]] == [
        "l01-first-hello" for _ in range(5)
    ]
    assert [item["outcome"] for item in reflections["recent"]] == [
        "avoided", "partly", "went_well", "avoided", "partly",
    ]
    assert [item["created_at"] for item in reflections["recent"]] == [
        f"2026-03-{index:02}T12:00:00+00:00" for index in range(6, 1, -1)
    ]
    assert all("note" not in item for item in reflections["recent"])
    assert "note" not in profile.text


def test_reflections_do_not_count_as_streak_activity(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        _save_reflection(client, "only-reflection", "went_well", "2026-03-01T12:00:00+00:00")
        response = client.get("/users/maya/streak")

    assert response.status_code == 200
    assert response.json()["streak_days"] == 0
    assert response.json()["active_today"] is False


def test_empty_profile_includes_an_empty_reflection_block(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        response = client.get("/users/maya/profile")

    assert response.status_code == 200
    assert response.json()["reflections"] == {
        "counts": {"went_well": 0, "partly": 0, "avoided": 0},
        "recent": [],
    }
