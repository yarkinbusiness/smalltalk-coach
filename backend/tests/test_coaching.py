from __future__ import annotations

import copy
from pathlib import Path

import anthropic
import httpx
import pytest
from fastapi.testclient import TestClient

from backend.app.content import load_curriculum
from backend.app.diagnosis import diagnose
from backend.app.main import create_app
from backend.app.routing import DIMENSION_ORDER, RoutingError, route_diagnosis
from backend.app.transcript import UnreadableTranscriptError, normalize_text


REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "content" / "lesson_path.json"
LESSONS_DIR = REPO_ROOT / "content" / "lessons"


class FakeAdapter:
    def __init__(self, *responses: object) -> None:
        self.responses = list(responses)
        self.calls = 0

    def request(self, transcript: dict[str, object]) -> object:
        self.calls += 1
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def _transcript() -> dict[str, object]:
    return normalize_text("Me: I just moved here last week.\nThem: How are you finding it?")


def _valid_diagnosis() -> dict[str, object]:
    quote_a = "I just moved here last week."
    quote_b = "How are you finding it?"
    return {
        "schema_version": 1,
        "dimensions": {
            "warmth": {"score": 3, "observations": []},
            "curiosity": {"score": 3, "observations": []},
            "reciprocity": {"score": 2, "observations": []},
            "flow": {"score": 3, "observations": []},
        },
        "strengths": [{"text": "You shared a concrete detail.", "turn_indices": [0], "quotes": [quote_a]}],
        "improvements": [{
            "dimension": "reciprocity", "priority": 1, "kind": "suggestion",
            "text": "After answering, make room for a related question.",
            "turn_indices": [0, 1], "quotes": [quote_a, quote_b],
        }],
        "small_practice_action": "In your next short chat, share one detail and ask one related follow-up.",
        "safety": {"status": "clear", "category": None},
    }


def _client(tmp_path: Path, adapter: FakeAdapter) -> TestClient:
    return TestClient(create_app(
        manifest_path=MANIFEST_PATH, lessons_dir=LESSONS_DIR,
        database_path=tmp_path / "progress.db", diagnosis_adapter=adapter,
    ))


def _request(client: TestClient, *, user_id: str = "maya", text: str = "Me: I just moved here last week.\nThem: How are you finding it?"):
    return client.post("/coaching/diagnoses", json={
        "user_id": user_id, "consent_to_process": True, "source": {"kind": "text", "text": text},
    })


def test_text_normalization_labeled_name_and_unlabeled() -> None:
    labelled = normalize_text("Me: Hello there\nAvery: Nice to meet you")
    assert labelled["user_speaker_id"] == "user"
    assert [(turn["speaker"], turn["speaker_id"]) for turn in labelled["turns"]] == [
        ("user", "user"), ("other", "other"),
    ]
    named = normalize_text("Avery: Hello there\nRin: Nice to meet you")
    assert named["user_speaker_id"] is None
    assert [turn["speaker"] for turn in named["turns"]] == ["unknown", "unknown"]
    blob = normalize_text("A conversation without supplied speaker labels.")
    assert blob["user_speaker_id"] is None
    assert blob["turns"] == [{"index": 0, "speaker_id": "unknown", "speaker": "unknown", "text": "A conversation without supplied speaker labels.", "source": "pasted"}]
    with pytest.raises(UnreadableTranscriptError):
        normalize_text(" \n \t ")


@pytest.mark.parametrize("mutate", [
    lambda item: item["dimensions"].pop("flow"),
    lambda item: item["dimensions"]["warmth"].__setitem__("score", 6),
    lambda item: item["strengths"][0].__setitem__("quotes", ["not in the transcript"]),
    lambda item: item["strengths"][0].__setitem__("turn_indices", [9]),
    lambda item: item.__setitem__("improvements", [copy.deepcopy(item["improvements"][0]) for _ in range(3)]),
    lambda item: item.__setitem__("improvements", [item["improvements"][0], {**copy.deepcopy(item["improvements"][0]), "dimension": "warmth"}]),
    lambda item: item.update({"small_practice_action": "Review l04-answer-and-return next."}),
])
def test_invalid_diagnosis_retries_once_then_returns_502(tmp_path: Path, mutate) -> None:
    payload = _valid_diagnosis()
    mutate(payload)
    fake = FakeAdapter(payload, payload)
    with _client(tmp_path, fake) as client:
        response = _request(client)
        assert response.status_code == 502
        assert response.json()["detail"] == "ai_unavailable"
        assert client.get("/coaching/reports", params={"user_id": "maya"}).json() == []
    assert fake.calls == 2


def test_valid_diagnosis_passes_validation() -> None:
    fake = FakeAdapter(_valid_diagnosis())
    assert diagnose(fake, _transcript(), {"l04-answer-and-return"})["dimensions"]["reciprocity"]["score"] == 2
    assert fake.calls == 1


def test_routing_lowest_ties_earliest_and_review() -> None:
    curriculum = load_curriculum(MANIFEST_PATH, LESSONS_DIR)
    diagnosis = _valid_diagnosis()
    result = route_diagnosis(diagnosis, curriculum, set())
    assert result["weakest_dimension"] == "reciprocity"
    assert result["lesson"]["id"] == "l04-answer-and-return"
    for index, winner in enumerate(DIMENSION_ORDER):
        tied = _valid_diagnosis()
        for dimension in DIMENSION_ORDER:
            tied["dimensions"][dimension]["score"] = 1 if DIMENSION_ORDER.index(dimension) >= index else 2
        assert route_diagnosis(tied, curriculum, set())["weakest_dimension"] == winner
    earliest = route_diagnosis(diagnosis, curriculum, {"l04-answer-and-return", "l05-show-you-heard"})
    assert earliest["lesson"]["id"] == "l06-follow-the-thread"
    completed = set(curriculum.routing["reciprocity"])
    review = route_diagnosis(diagnosis, curriculum, completed)
    assert review["lesson"]["id"] == "l04-answer-and-return"
    assert review["lesson"]["recommendation_kind"] == "review"
    broken = type("Broken", (), {"routing": {}, "lessons_by_id": curriculum.lessons_by_id})()
    with pytest.raises(RoutingError):
        route_diagnosis(diagnosis, broken, set())


def test_endpoint_happy_path_persists_and_reports_are_owned(tmp_path: Path) -> None:
    with _client(tmp_path, FakeAdapter(_valid_diagnosis())) as client:
        created = _request(client)
        assert created.status_code == 201
        report = created.json()
        assert report["status"] == "completed"
        assert report["recommendation"]["weakest_dimension"] == "reciprocity"
        assert report["recommendation"]["lesson"]["id"] == "l04-answer-and-return"
        assert report["practice_action"] == _valid_diagnosis()["small_practice_action"]
        report_id = report["id"]
        assert client.get(f"/coaching/reports/{report_id}", params={"user_id": "maya"}).status_code == 200
        assert client.get(f"/coaching/reports/{report_id}", params={"user_id": "other"}).status_code == 404
        summaries = client.get("/coaching/reports", params={"user_id": "maya"}).json()
        assert summaries == [{"id": report_id, "created_at": summaries[0]["created_at"], "source_kind": "text", "weakest_dimension": "reciprocity", "lesson_id": "l04-answer-and-return"}]
        assert client.delete(f"/coaching/reports/{report_id}", params={"user_id": "maya"}).status_code == 204
        assert client.get(f"/coaching/reports/{report_id}", params={"user_id": "maya"}).status_code == 404


def test_stored_recommendation_kind_does_not_change_after_lesson_completion(tmp_path: Path) -> None:
    with _client(tmp_path, FakeAdapter(_valid_diagnosis())) as client:
        created = _request(client)
        assert created.status_code == 201
        report = created.json()
        lesson_id = report["recommendation"]["lesson"]["id"]
        assert report["recommendation"]["lesson"]["recommendation_kind"] == "new"

        for lesson_to_complete in (
            "l01-first-hello",
            "l02-use-the-setting",
            "l03-easy-first-question",
            lesson_id,
        ):
            lesson = client.get(f"/lessons/{lesson_to_complete}", params={"user_id": "maya"})
            assert lesson.status_code == 200
            answers = {
                str(index): part["correct_option_index"]
                for index, part in enumerate(lesson.json()["completion_check"]["parts"])
                if part["kind"] == "choice"
            }
            completed = client.post(
                f"/lessons/{lesson_to_complete}/complete",
                json={"user_id": "maya", "answers": answers},
            )
            assert completed.status_code == 200
            assert completed.json()["completed"] is True

        fetched = client.get(f"/coaching/reports/{report['id']}", params={"user_id": "maya"})
        assert fetched.status_code == 200
        assert fetched.json()["recommendation"]["lesson"]["recommendation_kind"] == "new"


def test_endpoint_input_errors_and_no_persistence(tmp_path: Path) -> None:
    with _client(tmp_path, FakeAdapter(_valid_diagnosis())) as client:
        assert client.post("/coaching/diagnoses", json={"user_id": "maya", "consent_to_process": False, "source": {"kind": "text", "text": "hello"}}).json()["detail"] == "consent_required"
        screenshot = client.post("/coaching/diagnoses", json={"user_id": "maya", "consent_to_process": True, "source": {"kind": "screenshot"}})
        assert screenshot.status_code == 501 and screenshot.json()["detail"] == "screenshot_not_implemented"
        invalid = client.post("/coaching/diagnoses", json={"user_id": "maya", "consent_to_process": True, "source": {"kind": "audio"}})
        assert invalid.status_code == 400 and invalid.json()["detail"] == "invalid_request"
        assert _request(client, text="  \n").json()["detail"] == "unreadable_transcript"
        assert client.get("/coaching/reports", params={"user_id": "maya"}).json() == []


def test_refusal_provider_failure_and_escalation_do_not_persist(tmp_path: Path) -> None:
    class Refusal:
        stop_reason = "refusal"
        content = []
    request = httpx.Request("POST", "https://example.test")
    connection_error = anthropic.APIConnectionError(request=request)
    cases = [
        (FakeAdapter(Refusal()), 422, "coaching_refused"),
        (FakeAdapter(connection_error), 502, "ai_unavailable"),
        (FakeAdapter({**_valid_diagnosis(), "safety": {"status": "escalate", "category": "crisis"}}), 200, None),
    ]
    for index, (adapter, status, detail) in enumerate(cases):
        with _client(tmp_path / str(index), adapter) as client:
            response = _request(client)
            assert response.status_code == status
            if detail is not None:
                assert response.json()["detail"] == detail
            else:
                assert response.json()["status"] == "safety_guidance"
            assert client.get("/coaching/reports", params={"user_id": "maya"}).json() == []


def test_report_list_newest_first_and_health_key_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with _client(tmp_path, FakeAdapter(_valid_diagnosis(), _valid_diagnosis())) as client:
        first = _request(client).json()["id"]
        second = _request(client).json()["id"]
        summaries = client.get("/coaching/reports", params={"user_id": "maya"}).json()
        assert [summary["id"] for summary in summaries] == [second, first]
        assert client.get("/health").json()["coaching_enabled"] is False
        monkeypatch.setenv("ANTHROPIC_API_KEY", "set-for-test-only")
        assert client.get("/health").json()["coaching_enabled"] is True
