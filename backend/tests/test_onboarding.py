from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import create_app


REPO_ROOT = Path(__file__).resolve().parents[2]


def _client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(
        manifest_path=REPO_ROOT / "content" / "lesson_path.json",
        lessons_dir=REPO_ROOT / "content" / "lessons",
        database_path=tmp_path / "progress.db",
    ))


def _payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "goal": "meet_people_at_work",
        "context": "office",
        "baseline": {"warmth": 4, "curiosity": 2, "reciprocity": 3, "flow": 2},
    }
    payload.update(overrides)
    return payload


def test_onboarding_creates_and_derives_first_lowest_dimension_lesson(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        missing = client.get("/users/onboarding-user/onboarding")
        assert missing.status_code == 404
        assert missing.json() == {"detail": "not_onboarded"}

        created = client.post("/users/onboarding-user/onboarding", json=_payload())
        assert created.status_code == 201
        assert set(created.json()) == {"created_at"}

        response = client.get("/users/onboarding-user/onboarding")
    assert response.status_code == 200
    assert response.json() == {
        "goal": "meet_people_at_work",
        "context": "office",
        "baseline": {"warmth": 4, "curiosity": 2, "reciprocity": 3, "flow": 2},
        "emphasis": {
            "dimension": "curiosity",
            "lesson_id": "l03-easy-first-question",
            "title": "Ask an easy first question",
        },
    }


def test_onboarding_repost_replaces_record_without_progress_side_effects(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        first = client.post("/users/repost-user/onboarding", json=_payload())
        assert first.status_code == 201
        second = client.post(
            "/users/repost-user/onboarding",
            json=_payload(
                goal="keep_conversations_going",
                context="other",
                baseline={"warmth": 5, "curiosity": 4, "reciprocity": 3, "flow": 1},
            ),
        )
        assert second.status_code == 201
        assert second.json()["created_at"] >= first.json()["created_at"]

        onboarding = client.get("/users/repost-user/onboarding").json()
        assert onboarding["goal"] == "keep_conversations_going"
        assert onboarding["context"] == "other"
        assert onboarding["emphasis"]["dimension"] == "flow"
        assert client.get("/users/repost-user/profile").json()["report_count"] == 0
        assert client.get("/users/repost-user/streak").json()["streak_days"] == 0


def test_onboarding_rejects_invalid_goal(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        response = client.post("/users/invalid-goal/onboarding", json=_payload(goal="new_goal"))
    assert response.status_code == 422
    assert response.json() == {"detail": "invalid_goal"}


def test_onboarding_rejects_invalid_context(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        response = client.post("/users/invalid-context/onboarding", json=_payload(context="home"))
    assert response.status_code == 422
    assert response.json() == {"detail": "invalid_context"}


def test_onboarding_rejects_invalid_baseline(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        response = client.post(
            "/users/invalid-baseline/onboarding",
            json=_payload(baseline={"warmth": 1, "curiosity": 2, "reciprocity": 3}),
        )
        assert response.status_code == 422
        assert response.json() == {"detail": "invalid_baseline"}

        response = client.post(
            "/users/invalid-rating/onboarding",
            json=_payload(baseline={"warmth": 1, "curiosity": 2, "reciprocity": 3, "flow": True}),
        )
    assert response.status_code == 422
    assert response.json() == {"detail": "invalid_baseline"}
