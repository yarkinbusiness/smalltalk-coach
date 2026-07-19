from __future__ import annotations

import copy
import base64
from pathlib import Path

import anthropic
import httpx
import pytest
from fastapi.testclient import TestClient

from backend.app.content import load_curriculum
from backend.app import diagnosis
from backend.app import vision
from backend.app.coaching import _run_screenshot_job
from backend.app.diagnosis import diagnose
from backend.app.main import create_app
from backend.app.routing import DIMENSION_ORDER, RoutingError, route_diagnosis
from backend.app.transcript import UnreadableTranscriptError, normalize_text


REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "content" / "lesson_path.json"
LESSONS_DIR = REPO_ROOT / "content" / "lessons"


def test_coaching_model_is_haiku_and_app_source_has_no_forbidden_model_names() -> None:
    forbidden_names = ("son" + "net", "o" + "pus", "fa" + "ble", "my" + "thos")
    app_dir = REPO_ROOT / "backend" / "app"
    for source_file in app_dir.rglob("*.py"):
        source = source_file.read_text(encoding="utf-8").casefold()
        assert not any(name in source for name in forbidden_names), source_file
    assert diagnosis.COACHING_MODEL == "claude-haiku-4-5"


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


class FakeVisionAdapter:
    def __init__(self, *responses: object) -> None:
        self.responses = list(responses)
        self.calls = 0

    def request(self, *, media_type: str, image_base64: str, user_message_side: str) -> object:
        self.calls += 1
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def _transcript() -> dict[str, object]:
    return normalize_text("Me: I just moved here last week.\nThem: How are you finding it?")


def _valid_diagnosis() -> dict[str, object]:
    quote_a = "I just moved here last week."
    return {
        "schema_version": 1,
        "mode": "with_user_reply",
        "incoming_interpretation": {
            "tone": "Warm and interested.",
            "intent": "The other person is inviting the user to share their experience.",
            "response_goals": "Share one detail and make an easy next thread.",
        },
        "response_coaching": {
            "guidance": "Answer with one detail, then invite a related exchange.",
            "example_responses": ["It has been a fun adjustment so far. Have you lived here long?"],
        },
        "transferable_takeaway": "One concrete detail plus a related question keeps an exchange moving.",
        "focus_dimension": "reciprocity",
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
            "turn_indices": [0], "quotes": [quote_a],
        }],
        "small_practice_action": "In your next short chat, share one detail and ask one related follow-up.",
        "safety": {"status": "clear", "category": None},
    }


def _valid_stimulus_diagnosis() -> dict[str, object]:
    return {
        "schema_version": 1,
        "mode": "stimulus_only",
        "incoming_interpretation": {
            "tone": "Warm and curious.",
            "intent": "The other person is inviting an update.",
            "response_goals": "Offer one specific detail and keep the conversation open.",
        },
        "response_coaching": {
            "guidance": "Answer directly, add one concrete detail, and return a light question.",
            "example_responses": [
                "I am settling in well — I have already found a favorite café. How about you?",
                "Pretty well so far; I am still exploring the neighborhood. What do you like most about it?",
            ],
        },
        "transferable_takeaway": "A brief update plus a related question makes an incoming check-in easy to continue.",
        "focus_dimension": "curiosity",
        "dimensions": None,
        "strengths": [],
        "improvements": [],
        "small_practice_action": "Practice adding one easy return question after a short update.",
        "safety": {"status": "clear", "category": None},
    }


def _client(tmp_path: Path, adapter: FakeAdapter, vision_adapter: FakeVisionAdapter | None = None) -> TestClient:
    app = create_app(
        manifest_path=MANIFEST_PATH, lessons_dir=LESSONS_DIR,
        database_path=tmp_path / "progress.db", diagnosis_adapter=adapter,
    )
    if vision_adapter is not None:
        app.state.vision_adapter = vision_adapter
    return TestClient(app)


def _request(client: TestClient, *, user_id: str = "maya", text: str = "Me: I just moved here last week.\nThem: How are you finding it?"):
    return client.post("/coaching/diagnoses", json={
        "user_id": user_id, "consent_to_process": True, "source": {"kind": "text", "text": text},
    })


_TINY_PNG = base64.b64encode(
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0dIDATx\x9cc\xf8\xcf\xc0\xf0\x1f\x00\x05\x00\x01\xff\x89\x99=\x1d\x00\x00\x00\x00IEND\xaeB`\x82"
).decode()


def _valid_extraction(*, side: str = "right") -> dict[str, object]:
    if side == "unknown":
        return {
            "schema_version": 1, "source_kind": "screenshot", "user_speaker_id": None,
            "turns": [
                {"index": 0, "speaker_id": "other", "speaker": "other", "text": "I just moved here last week.", "source": "vision"},
                {"index": 1, "speaker_id": "other", "speaker": "other", "text": "How are you finding it?", "source": "vision"},
            ],
        }
    return {
        "schema_version": 1, "source_kind": "screenshot", "user_speaker_id": "user",
        "turns": [
            {"index": 0, "speaker_id": "user", "speaker": "user", "text": "I just moved here last week.", "source": "vision"},
            {"index": 1, "speaker_id": "other", "speaker": "other", "text": "How are you finding it?", "source": "vision"},
        ],
    }


def _screenshot_request(client: TestClient, *, user_id: str = "maya", image_base64: str = _TINY_PNG, media_type: str = "image/png", side: str | None = "right"):
    source: dict[str, object] = {"kind": "screenshot", "media_type": media_type, "image_base64": image_base64}
    if side is not None:
        source["user_message_side"] = side
    return client.post("/coaching/diagnoses", json={"user_id": user_id, "consent_to_process": True, "source": source})


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
    assert blob["turns"] == [{"index": 0, "speaker_id": "other", "speaker": "other", "text": "A conversation without supplied speaker labels.", "source": "pasted"}]
    with pytest.raises(UnreadableTranscriptError):
        normalize_text(" \n \t ")


@pytest.mark.parametrize("mutate", [
    lambda item: item["dimensions"].pop("flow"),
    lambda item: item["dimensions"]["warmth"].__setitem__("score", 6),
    lambda item: item["strengths"][0].__setitem__("quotes", ["not in the transcript"]),
    lambda item: item["strengths"][0].__setitem__("turn_indices", [9]),
    lambda item: item.__setitem__("improvements", [item["improvements"][0], {**copy.deepcopy(item["improvements"][0]), "dimension": "warmth"}]),
    lambda item: item.__setitem__("improvements", []),
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


def test_stimulus_only_question_routes_persists_and_serves_response_coaching(tmp_path: Path) -> None:
    text = "How are you settling in so far?"
    with _client(tmp_path, FakeAdapter(_valid_stimulus_diagnosis())) as client:
        created = _request(client, text=text)
        assert created.status_code == 201
        report = created.json()
        assert report["transcript"]["turns"][0]["speaker"] == "other"
        assert report["diagnosis"]["mode"] == "stimulus_only"
        assert report["diagnosis"]["dimensions"] is None
        assert report["diagnosis"]["response_coaching"]["example_responses"] == _valid_stimulus_diagnosis()["response_coaching"]["example_responses"]
        assert report["diagnosis"]["transferable_takeaway"]
        assert report["recommendation"]["weakest_dimension"] == "curiosity"
        assert report["recommendation"]["selection_reason"] == "focus_dimension"
        stored = client.get(f"/coaching/reports/{report['id']}", params={"user_id": "maya"})
        assert stored.json()["diagnosis"]["incoming_interpretation"] == report["diagnosis"]["incoming_interpretation"]


def test_stimulus_only_rejects_dimension_scores() -> None:
    scored_stimulus = _valid_diagnosis()
    scored_stimulus["mode"] = "with_user_reply"
    with pytest.raises(ValueError, match="mode does not match transcript"):
        diagnosis.validate_diagnosis(scored_stimulus, normalize_text("How are you settling in so far?"), set())


def test_with_user_reply_rejects_other_evidence_and_wrong_focus_dimension() -> None:
    other_evidence = _valid_diagnosis()
    other_evidence["dimensions"]["warmth"]["observations"] = [{
        "kind": "observation", "text": "The user was asked a question.",
        "turn_indices": [1], "quotes": ["How are you finding it?"],
    }]
    with pytest.raises(ValueError, match="user turns"):
        diagnosis.validate_diagnosis(other_evidence, _transcript(), set())

    wrong_focus = _valid_diagnosis()
    wrong_focus["focus_dimension"] = "warmth"
    with pytest.raises(ValueError, match="focus dimension"):
        diagnosis.validate_diagnosis(wrong_focus, _transcript(), set())


def test_stimulus_only_allows_empty_improvements_but_with_user_reply_does_not() -> None:
    assert diagnosis.validate_diagnosis(_valid_stimulus_diagnosis(), normalize_text("How are you settling in so far?"), set())["improvements"] == []
    with_user_reply = _valid_diagnosis()
    with_user_reply["improvements"] = []
    with pytest.raises(ValueError, match="invalid improvements"):
        diagnosis.validate_diagnosis(with_user_reply, _transcript(), set())


def test_empty_quotes_for_missing_behavior_are_accepted() -> None:
    payload = _valid_diagnosis()
    payload["improvements"][0].update({
        "kind": "observation",
        "text": "You do not ask a follow-up question.",
        "quotes": [],
    })
    validated = diagnosis.validate_diagnosis(payload, _transcript(), set())
    assert validated["improvements"][0]["quotes"] == []


@pytest.mark.parametrize("count", [3, 4])
def test_over_returned_improvements_are_coerced_and_persisted(tmp_path: Path, count: int) -> None:
    payload = _valid_diagnosis()
    improvements = []
    for priority in (3, 1, 2, 4)[:count]:
        improvement = copy.deepcopy(payload["improvements"][0])
        improvement["priority"] = priority
        improvement["text"] = f"Improvement {priority}."
        improvements.append(improvement)
    payload["improvements"] = improvements
    with _client(tmp_path, FakeAdapter(payload)) as client:
        created = _request(client)
        assert created.status_code == 201
        report = created.json()
        assert [item["text"] for item in report["diagnosis"]["improvements"]] == ["Improvement 1.", "Improvement 2."]
        assert [item["priority"] for item in report["diagnosis"]["improvements"]] == [1, 2]
        stored = client.get(f"/coaching/reports/{report['id']}", params={"user_id": "maya"})
        assert stored.json()["diagnosis"]["improvements"] == report["diagnosis"]["improvements"]


def test_four_strengths_are_truncated_to_three_and_persisted(tmp_path: Path) -> None:
    payload = _valid_diagnosis()
    payload["strengths"] = [
        {**copy.deepcopy(payload["strengths"][0]), "text": f"Strength {index}."}
        for index in range(1, 5)
    ]
    with _client(tmp_path, FakeAdapter(payload)) as client:
        created = _request(client)
        assert created.status_code == 201
        report = created.json()
        assert [item["text"] for item in report["diagnosis"]["strengths"]] == ["Strength 1.", "Strength 2.", "Strength 3."]
        stored = client.get(f"/coaching/reports/{report['id']}", params={"user_id": "maya"})
        assert stored.json()["diagnosis"]["strengths"] == report["diagnosis"]["strengths"]


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


def test_routing_uses_focus_dimension_when_scores_are_absent() -> None:
    curriculum = load_curriculum(MANIFEST_PATH, LESSONS_DIR)
    result = route_diagnosis(_valid_stimulus_diagnosis(), curriculum, set())
    assert result["weakest_dimension"] == "curiosity"
    assert result["selection_reason"] == "focus_dimension"
    assert result["lesson"]["id"] == "l03-easy-first-question"


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
        assert screenshot.status_code == 400 and screenshot.json()["detail"] == "invalid_request"
        invalid = client.post("/coaching/diagnoses", json={"user_id": "maya", "consent_to_process": True, "source": {"kind": "audio"}})
        assert invalid.status_code == 400 and invalid.json()["detail"] == "invalid_request"
        assert _request(client, text="  \n").json()["detail"] == "unreadable_transcript"
        assert client.get("/coaching/reports", params={"user_id": "maya"}).json() == []


@pytest.mark.parametrize("media_type,image_base64,status,detail", [
    ("image/gif", _TINY_PNG, 415, "unsupported_image_type"),
    ("image/png", base64.b64encode(b"\x89PNG" + b"x" * (10 * 1024 * 1024 + 1)).decode(), 413, "image_too_large"),
    ("image/png", "not-valid-base64", 422, "bad_image"),
    ("image/png", base64.b64encode(b"not a png").decode(), 422, "bad_image"),
])
def test_screenshot_image_validation_runs_before_vision(
    tmp_path: Path, media_type: str, image_base64: str, status: int, detail: str,
) -> None:
    fake_vision = FakeVisionAdapter(_valid_extraction())
    with _client(tmp_path, FakeAdapter(_valid_diagnosis()), fake_vision) as client:
        response = _screenshot_request(client, media_type=media_type, image_base64=image_base64)
        assert response.status_code == status
        assert response.json()["detail"] == detail
    assert fake_vision.calls == 0


def test_screenshot_job_completes_with_persisted_report_and_no_image_record(tmp_path: Path) -> None:
    fake_vision = FakeVisionAdapter(_valid_extraction())
    with _client(tmp_path, FakeAdapter(_valid_diagnosis()), fake_vision) as client:
        # Create a job directly to observe its processing state before its worker runs.
        app = client.app
        job = app.state.coaching_jobs.create("maya")
        assert app.state.coaching_jobs.get(job["id"], "maya") == job
        assert "image" not in app.state.coaching_jobs._jobs[job["id"]]
        _run_screenshot_job(app, job["id"], "maya", "image/png", _TINY_PNG, "right")
        completed = client.get(f"/coaching/diagnoses/jobs/{job['id']}", params={"user_id": "maya"})
        assert completed.status_code == 200
        report = completed.json()
        assert report["status"] == "completed"
        assert report["transcript"]["source_kind"] == "screenshot"
        assert report["transcript"]["turns"][0]["text"] == "I just moved here last week."
        assert report["diagnosis"]["small_practice_action"] == _valid_diagnosis()["small_practice_action"]
        assert "image" not in app.state.coaching_jobs._jobs[job["id"]]


def test_screenshot_post_returns_202_poll_url_and_background_result(tmp_path: Path) -> None:
    fake_vision = FakeVisionAdapter(_valid_extraction())
    with _client(tmp_path, FakeAdapter(_valid_diagnosis()), fake_vision) as client:
        created = _screenshot_request(client)
        assert created.status_code == 202
        payload = created.json()
        assert payload["job_id"].startswith("cj_")
        assert payload["poll_url"] == f"/coaching/diagnoses/jobs/{payload['job_id']}"
        completed = client.get(payload["poll_url"], params={"user_id": "maya"})
        assert completed.json()["status"] == "completed"


@pytest.mark.parametrize("mutate", [
    lambda item: item["turns"][1].__setitem__("index", 2),
    lambda item: item["turns"][0].__setitem__("speaker", "invalid"),
    lambda item: item.__setitem__("turns", []),
])
def test_invalid_screenshot_extraction_fails_unreadable(tmp_path: Path, mutate) -> None:
    extraction = _valid_extraction()
    mutate(extraction)
    with _client(tmp_path, FakeAdapter(_valid_diagnosis()), FakeVisionAdapter(extraction)) as client:
        job = client.app.state.coaching_jobs.create("maya")
        _run_screenshot_job(client.app, job["id"], "maya", "image/png", _TINY_PNG, "right")
        assert client.get(f"/coaching/diagnoses/jobs/{job['id']}", params={"user_id": "maya"}).json() == {
            "status": "failed", "detail": "unreadable_transcript",
        }


def test_screenshot_provider_failure_and_refusal_are_safe_job_results(tmp_path: Path) -> None:
    request = httpx.Request("POST", "https://example.test")
    cases = [
        (FakeVisionAdapter(anthropic.APIConnectionError(request=request)), "ai_unavailable"),
        (FakeVisionAdapter({"stop_reason": "refusal", "content": []}), "coaching_refused"),
    ]
    for index, (fake_vision, expected) in enumerate(cases):
        with _client(tmp_path / str(index), FakeAdapter(_valid_diagnosis()), fake_vision) as client:
            job = client.app.state.coaching_jobs.create("maya")
            _run_screenshot_job(client.app, job["id"], "maya", "image/png", _TINY_PNG, "right")
            assert client.get(f"/coaching/diagnoses/jobs/{job['id']}", params={"user_id": "maya"}).json() == {
                "status": "failed", "detail": expected,
            }


def test_screenshot_attribution_unknown_side_and_polling_ownership(tmp_path: Path) -> None:
    with _client(tmp_path, FakeAdapter(_valid_stimulus_diagnosis()), FakeVisionAdapter(_valid_extraction(side="unknown"))) as client:
        created = _screenshot_request(client, side=None).json()
        report = client.get(created["poll_url"], params={"user_id": "maya"}).json()
        assert report["transcript"]["user_speaker_id"] is None
        assert all(turn["speaker"] == "other" for turn in report["transcript"]["turns"])
        assert report["recommendation"]["selection_reason"] == "focus_dimension"
        assert client.get(created["poll_url"], params={"user_id": "other"}).status_code == 404
        assert client.get("/coaching/diagnoses/jobs/cj_missing", params={"user_id": "maya"}).status_code == 404


def test_screenshot_escalation_returns_guidance_without_report(tmp_path: Path) -> None:
    escalated = {**_valid_diagnosis(), "safety": {"status": "escalate", "category": "crisis"}}
    with _client(tmp_path, FakeAdapter(escalated), FakeVisionAdapter(_valid_extraction())) as client:
        job = client.app.state.coaching_jobs.create("maya")
        _run_screenshot_job(client.app, job["id"], "maya", "image/png", _TINY_PNG, "right")
        result = client.get(f"/coaching/diagnoses/jobs/{job['id']}", params={"user_id": "maya"}).json()
        assert result["status"] == "safety_guidance"
        assert result["category"] == "crisis"
        assert client.get("/coaching/reports", params={"user_id": "maya"}).json() == []


def test_vision_uses_locked_coaching_model() -> None:
    assert vision.COACHING_MODEL == diagnosis.COACHING_MODEL


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
