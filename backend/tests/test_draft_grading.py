from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

import anthropic
import httpx
import pytest
from fastapi.testclient import TestClient

from backend.app.draft_grading import (
    BudgetExceededError,
    DraftGradingBudget,
    DraftGradingError,
    DraftGradingRefusedError,
    grade_draft,
)
from backend.app.main import create_app


REPO_ROOT = Path(__file__).resolve().parents[2]


class FakeDraftGradingAdapter:
    def __init__(self, *responses: object) -> None:
        self.responses = list(responses)
        self.calls = 0

    def request(self, prompt: str, good_answer_demonstrates: str, draft: str) -> object:
        self.calls += 1
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def _response(
    *, met_criteria: bool = True, feedback: str = "Your shared cue makes the opening easy to answer.",
    input_tokens: int = 100, output_tokens: int = 50,
) -> dict[str, object]:
    return {
        "content": [{"text": json.dumps({"met_criteria": met_criteria, "feedback": feedback})}],
        "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
    }


def _provider_status_error(status_code: int) -> anthropic.APIStatusError:
    request = httpx.Request("POST", "https://example.test/messages")
    response = httpx.Response(status_code, request=request)
    return anthropic.APIStatusError("provider failure", response=response, body=None)


def _grade(adapter: FakeDraftGradingAdapter, budget: DraftGradingBudget | None = None) -> dict[str, object]:
    return grade_draft(
        adapter,
        budget or DraftGradingBudget(5.00),
        "Draft an opening.",
        "A shared cue.",
        "Hi, this line is moving slowly today.",
        now=datetime(2026, 7, 21, tzinfo=UTC),
    )


def test_draft_grading_budget_tracks_calendar_month_spend_and_resets() -> None:
    budget = DraftGradingBudget(5.00)
    july = datetime(2026, 7, 21, tzinfo=UTC)
    august = datetime(2026, 8, 1, tzinfo=UTC)

    assert budget.has_room(july)
    budget.record_cost(5.00, july)
    assert not budget.has_room(july)
    assert budget.has_room(august)
    assert budget._spent_usd == 0.0


def test_draft_grading_budget_rolls_resets_at_over_december() -> None:
    budget = DraftGradingBudget(5.00)

    assert budget.resets_at(datetime(2026, 12, 31, 23, 59, tzinfo=UTC)) == datetime(
        2027, 1, 1, tzinfo=UTC
    )


def test_grade_draft_returns_valid_grading() -> None:
    fake = FakeDraftGradingAdapter(_response())

    assert _grade(fake) == {
        "met_criteria": True,
        "feedback": "Your shared cue makes the opening easy to answer.",
    }
    assert fake.calls == 1


def test_grade_draft_retries_transient_provider_errors() -> None:
    fake = FakeDraftGradingAdapter(_provider_status_error(500), _provider_status_error(500), _response())

    assert _grade(fake)["met_criteria"] is True
    assert fake.calls == 3


def test_grade_draft_does_not_retry_non_transient_provider_error() -> None:
    fake = FakeDraftGradingAdapter(_provider_status_error(400), _response())

    with pytest.raises(DraftGradingError):
        _grade(fake)
    assert fake.calls == 1


def test_grade_draft_refusal_is_metered_without_retrying() -> None:
    budget = DraftGradingBudget(5.00)
    fake = FakeDraftGradingAdapter({
        "stop_reason": "refusal",
        "usage": {"input_tokens": 100, "output_tokens": 50},
    })

    with pytest.raises(DraftGradingRefusedError):
        _grade(fake, budget)
    assert fake.calls == 1
    assert budget._spent_usd > 0


def test_grade_draft_raises_after_exhausting_transient_errors() -> None:
    fake = FakeDraftGradingAdapter(*[_provider_status_error(500) for _ in range(3)])

    with pytest.raises(DraftGradingError):
        _grade(fake)
    assert fake.calls == 3


def test_grade_draft_rejects_before_request_when_monthly_budget_is_exhausted() -> None:
    moment = datetime(2026, 7, 21, tzinfo=UTC)
    budget = DraftGradingBudget(1.00)
    budget.record_cost(1.00, moment)
    fake = FakeDraftGradingAdapter(_response())

    with pytest.raises(BudgetExceededError):
        _grade(fake, budget)
    assert fake.calls == 0


def _client(tmp_path: Path, adapter: FakeDraftGradingAdapter) -> TestClient:
    return TestClient(create_app(
        manifest_path=REPO_ROOT / "content" / "lesson_path.json",
        lessons_dir=REPO_ROOT / "content" / "lessons",
        database_path=tmp_path / "progress.db",
        draft_grading_adapter=adapter,
    ))


def _request(client: TestClient, lesson_id: str = "l01-first-hello", **body: object):
    return client.post(f"/lessons/{lesson_id}/draft-grading", json={
        "user_id": "maya",
        "part_index": 1,
        "draft": "Hi, this waiting area is busy today.",
        **body,
    })


def test_draft_grading_endpoint_returns_feedback(tmp_path: Path) -> None:
    with _client(tmp_path, FakeDraftGradingAdapter(_response())) as client:
        response = _request(client)

    assert response.status_code == 200
    assert response.json() == {
        "met_criteria": True,
        "feedback": "Your shared cue makes the opening easy to answer.",
    }


def test_draft_grading_endpoint_validates_lesson_part_and_draft(tmp_path: Path) -> None:
    with _client(tmp_path, FakeDraftGradingAdapter(_response())) as client:
        missing = _request(client, "missing")
        wrong_part = _request(client, part_index=0)
        empty = _request(client, draft=" \n ")
        oversized = _request(client, draft="x" * 2001)

    assert missing.status_code == 404
    assert missing.json() == {"detail": "lesson_not_found"}
    assert wrong_part.status_code == 422
    assert wrong_part.json() == {"detail": "invalid_part"}
    assert empty.status_code == 422
    assert empty.json() == {"detail": "invalid_draft"}
    assert oversized.status_code == 422
    assert oversized.json() == {"detail": "invalid_draft"}


def test_draft_grading_endpoint_reports_budget_exceeded(tmp_path: Path) -> None:
    with _client(tmp_path, FakeDraftGradingAdapter(_response())) as client:
        budget = DraftGradingBudget(1.00)
        budget.record_cost(1.00, datetime.now(UTC))
        client.app.state.draft_grading_budget = budget
        response = _request(client)

    assert response.status_code == 503
    assert response.json()["detail"] == "draft_grading_budget_exceeded"
    assert response.json()["resets_at"]
