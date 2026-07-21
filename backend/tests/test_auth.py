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


def _routes(client: TestClient, headers: dict[str, str] | None = None) -> list[int]:
    return [
        client.get("/curriculum", params={"user_id": "maya"}, headers=headers).status_code,
        client.get("/coaching/reports", params={"user_id": "maya"}, headers=headers).status_code,
        client.get("/users/maya/streak", headers=headers).status_code,
    ]


def test_auth_is_disabled_when_token_is_unset(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("SMALLTALK_API_TOKEN", raising=False)
    with _client(tmp_path) as client:
        assert client.get("/health").json()["auth_enabled"] is False
        assert _routes(client) == [200, 200, 200]


def test_auth_rejects_invalid_bearer_headers_and_accepts_correct_token(monkeypatch, tmp_path: Path) -> None:
    token = "test-shared-secret"
    monkeypatch.setenv("SMALLTALK_API_TOKEN", token)
    with _client(tmp_path) as client:
        assert client.get("/health").json()["auth_enabled"] is True
        for headers in (None, {"Authorization": "Bearer wrong"}, {"Authorization": "Basic token"}):
            for path, params in (
                ("/curriculum", {"user_id": "maya"}),
                ("/coaching/reports", {"user_id": "maya"}),
                ("/users/maya/streak", None),
            ):
                response = client.get(path, params=params, headers=headers)
                assert response.status_code == 401
                assert response.json() == {"detail": "unauthorized"}
        assert _routes(client, {"Authorization": f"Bearer {token}"}) == [200, 200, 200]


def test_rejected_request_does_not_run_route_handler(monkeypatch, tmp_path: Path) -> None:
    token = "test-shared-secret"
    headers = {"Authorization": f"Bearer {token}"}
    monkeypatch.setenv("SMALLTALK_API_TOKEN", token)
    with _client(tmp_path) as client:
        rejected = client.post("/users/maya/reflections", json={
            "subject_kind": "lesson",
            "subject_id": "l01-first-hello",
            "outcome": "went_well",
            "note": "A note that must not be stored.",
        }, headers={"Authorization": "Bearer wrong"})
        assert rejected.status_code == 401
        assert rejected.json() == {"detail": "unauthorized"}
        assert client.get("/users/maya/reflections", headers=headers).json() == {"reflections": []}
