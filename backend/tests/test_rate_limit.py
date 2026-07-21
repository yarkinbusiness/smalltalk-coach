from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import coaching
from backend.app.main import create_app


REPO_ROOT = Path(__file__).resolve().parents[2]


class _FrozenDatetime:
    current = datetime(2026, 1, 1, tzinfo=UTC)

    @classmethod
    def now(cls, timezone: object) -> datetime:
        assert timezone is UTC
        return cls.current


def _client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(
        manifest_path=REPO_ROOT / "content" / "lesson_path.json",
        lessons_dir=REPO_ROOT / "content" / "lessons",
        database_path=tmp_path / "progress.db",
    ))


def _request(client: TestClient, user_id: str = "maya"):
    return client.post("/coaching/diagnoses", json={
        "user_id": user_id,
        "consent_to_process": True,
        "source": {"kind": "text", "text": "How are you finding it?"},
    })


def _safe_diagnosis(*_args: object) -> dict[str, object]:
    return {"safety": {"status": "escalate", "category": "other"}}


def test_diagnosis_rate_limit_resets_after_its_fixed_window(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("SMALLTALK_API_TOKEN", raising=False)
    monkeypatch.setenv("SMALLTALK_COACHING_RATE_LIMIT", "2")
    monkeypatch.setenv("SMALLTALK_COACHING_RATE_WINDOW_SECONDS", "60")
    monkeypatch.setattr(coaching, "datetime", _FrozenDatetime)
    monkeypatch.setattr(coaching, "diagnose", _safe_diagnosis)
    _FrozenDatetime.current = datetime(2026, 1, 1, tzinfo=UTC)

    with _client(tmp_path) as client:
        assert _request(client).status_code == 200
        assert _request(client).status_code == 200
        limited = _request(client)
        assert limited.status_code == 429
        assert limited.json() == {"detail": "rate_limited"}
        assert int(limited.headers["Retry-After"]) >= 1

        _FrozenDatetime.current += timedelta(seconds=60)
        assert _request(client).status_code == 200


def test_diagnosis_rate_limit_is_per_user_and_other_coaching_routes_are_unaffected(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("SMALLTALK_API_TOKEN", raising=False)
    monkeypatch.setenv("SMALLTALK_COACHING_RATE_LIMIT", "1")
    monkeypatch.setattr(coaching, "diagnose", _safe_diagnosis)

    with _client(tmp_path) as client:
        assert _request(client, "maya").status_code == 200
        assert _request(client, "maya").status_code == 429
        assert _request(client, "other").status_code == 200

        job = client.app.state.coaching_jobs.create("maya")
        assert client.get("/coaching/reports", params={"user_id": "maya"}).status_code == 200
        assert client.get(f"/coaching/diagnoses/jobs/{job['id']}", params={"user_id": "maya"}).status_code == 200
        assert client.delete("/coaching/reports/missing", params={"user_id": "maya"}).status_code == 404


def test_failed_diagnosis_still_counts_toward_the_rate_limit(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("SMALLTALK_API_TOKEN", raising=False)
    monkeypatch.setenv("SMALLTALK_COACHING_RATE_LIMIT", "1")

    def unavailable(*_args: object) -> dict[str, object]:
        raise coaching.DiagnosisError()

    monkeypatch.setattr(coaching, "diagnose", unavailable)
    with _client(tmp_path) as client:
        assert _request(client).status_code == 502
        assert _request(client).status_code == 429


@pytest.mark.parametrize(("limit", "window", "expected_limit", "expected_window"), [
    ("garbage", "garbage", 10, 60),
    ("0", "-1", 10, 60),
    ("2", "garbage", 2, 60),
    ("garbage", "2", 10, 2),
])
def test_rate_limit_environment_falls_back_safely(
    monkeypatch, tmp_path: Path, limit: str, window: str, expected_limit: int, expected_window: int,
) -> None:
    monkeypatch.delenv("SMALLTALK_API_TOKEN", raising=False)
    monkeypatch.setenv("SMALLTALK_COACHING_RATE_LIMIT", limit)
    monkeypatch.setenv("SMALLTALK_COACHING_RATE_WINDOW_SECONDS", window)

    with _client(tmp_path) as client:
        limiter = client.app.state.coaching_rate_limiter
        assert limiter.limit == expected_limit
        assert limiter.window_seconds == expected_window
