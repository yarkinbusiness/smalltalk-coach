from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.diagnosis import DIMENSIONS
from backend.app.main import create_app


REPO_ROOT = Path(__file__).resolve().parents[2]


def _client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(
        manifest_path=REPO_ROOT / "content" / "lesson_path.json",
        lessons_dir=REPO_ROOT / "content" / "lessons",
        database_path=tmp_path / "progress.db",
    ))


def _save_report(client: TestClient, report_id: str, user_id: str) -> None:
    client.app.state.progress_store.save_coaching_report(
        report_id=report_id,
        user_id=user_id,
        transcript={"source_kind": "text"},
        diagnosis={"mode": "stimulus_only", "dimensions": None},
        weakest_dimension="reciprocity",
        lesson_id="l04-answer-and-return",
        recommendation_kind="new",
        practice_action="Practice one follow-up.",
    )


def _save_reflection(client: TestClient, reflection_id: str, user_id: str) -> None:
    client.app.state.progress_store.save_reflection(
        reflection_id=reflection_id,
        user_id=user_id,
        subject_kind="lesson",
        subject_id="l01-first-hello",
        outcome="went_well",
        note="private note",
    )


def test_delete_coaching_data_removes_reports_reflections_and_resets_profile(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        _save_report(client, "report-1", "maya")
        _save_report(client, "report-2", "maya")
        _save_reflection(client, "reflection-1", "maya")

        deleted = client.delete("/users/maya/coaching-data")

        assert deleted.status_code == 200
        assert deleted.json() == {"reports_deleted": 2, "reflections_deleted": 1}
        assert client.get("/coaching/reports", params={"user_id": "maya"}).json() == []
        assert client.get("/users/maya/reflections").json() == {"reflections": []}
        assert client.get("/users/maya/profile").json() == {
            "report_count": 0,
            "dimensions": {
                dimension: {"scores": [], "flagged_count": 0} for dimension in DIMENSIONS
            },
            "recurring_weakness": None,
            "lessons": {"completed_count": 0, "recommended_not_taken": []},
            "reflections": {
                "counts": {"went_well": 0, "partly": 0, "avoided": 0},
                "recent": [],
            },
        }


def test_delete_coaching_data_keeps_learning_progress_review_and_onboarding(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        store = client.app.state.progress_store
        store.record_completion("maya", "l01-first-hello")
        store.record_review("maya", "l01-first-hello")
        onboarding = client.post("/users/maya/onboarding", json={
            "goal": "meet_people_at_work",
            "context": "office",
            "baseline": {"warmth": 4, "curiosity": 2, "reciprocity": 3, "flow": 2},
        })
        assert onboarding.status_code == 201
        streak_before = client.get("/users/maya/streak").json()
        curriculum_before = client.get("/curriculum", params={"user_id": "maya"}).json()
        onboarding_before = client.get("/users/maya/onboarding").json()

        deleted = client.delete("/users/maya/coaching-data")

        assert deleted.json() == {"reports_deleted": 0, "reflections_deleted": 0}
        assert client.get("/users/maya/streak").json() == streak_before
        assert client.get("/curriculum", params={"user_id": "maya"}).json() == curriculum_before
        assert client.get("/users/maya/onboarding").json() == onboarding_before


def test_delete_coaching_data_is_idempotent(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        _save_report(client, "report-1", "maya")
        _save_reflection(client, "reflection-1", "maya")

        first = client.delete("/users/maya/coaching-data")
        second = client.delete("/users/maya/coaching-data")

    assert first.status_code == second.status_code == 200
    assert first.json() == {"reports_deleted": 1, "reflections_deleted": 1}
    assert second.json() == {"reports_deleted": 0, "reflections_deleted": 0}


def test_delete_coaching_data_is_scoped_to_its_owner(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        _save_report(client, "maya-report", "maya")
        _save_reflection(client, "maya-reflection", "maya")
        _save_report(client, "other-report", "other")
        _save_reflection(client, "other-reflection", "other")

        deleted = client.delete("/users/maya/coaching-data")

        assert deleted.json() == {"reports_deleted": 1, "reflections_deleted": 1}
        assert client.get("/coaching/reports", params={"user_id": "maya"}).json() == []
        assert client.get("/users/maya/reflections").json() == {"reflections": []}
        assert [report["id"] for report in client.get("/coaching/reports", params={"user_id": "other"}).json()] == ["other-report"]
        assert [reflection["id"] for reflection in client.get("/users/other/reflections").json()["reflections"]] == ["other-reflection"]
