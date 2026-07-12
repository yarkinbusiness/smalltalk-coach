"""T6: POST .../end's state machine (active/grading/ended/failed) and the
min-turns guard, driven through the real FastAPI routes against the
in-process TestClient + FakeAnthropic (no real network calls, no real
threading needed for these -- see test_end_session_async.py for the test
that specifically proves grading runs *after* the 202 response is sent,
which requires a real server since TestClient runs BackgroundTasks
synchronously within the request/response cycle).
"""

import json

from app import db
from fake_anthropic import agent_message_event, idle_event


def _start_session(client, user_id="turns-user", scenario_id="coffee-shop-line") -> str:
    resp = client.post("/practice/sessions", json={"user_id": user_id, "scenario_id": scenario_id})
    assert resp.status_code == 200
    return resp.json()["session_id"]


def _send_user_turns(client, fake_client, session_id: str, count: int) -> None:
    for i in range(count):
        fake_client.queue_message_stream(["ok"])
        resp = client.post(
            f"/practice/sessions/{session_id}/message", json={"text": f"turn {i}"}
        )
        assert resp.status_code == 200


# --- 422: fewer than 3 user turns -------------------------------------------


def test_end_with_fewer_than_3_user_turns_returns_422_and_never_touches_coordinator(
    client, fake_client
):
    session_id = _start_session(client)
    _send_user_turns(client, fake_client, session_id, count=2)  # one short of the minimum

    resp = client.post(f"/practice/sessions/{session_id}/end")

    assert resp.status_code == 422
    # The coordinator (a real CMA sandboxed session in production) must never
    # be touched for a conversation this short.
    assert fake_client.sessions_create_calls == []
    assert fake_client.sessions_events_stream_calls == []

    # Session is untouched -- still 'active', not silently bumped to 'grading'.
    row = db.get_practice_session(session_id)
    assert row["status"] == "active"


def test_end_with_zero_user_turns_returns_422(client, fake_client):
    session_id = _start_session(client)

    resp = client.post(f"/practice/sessions/{session_id}/end")

    assert resp.status_code == 422
    assert fake_client.sessions_create_calls == []


# --- 409: already grading / already ended -----------------------------------


def test_end_while_already_grading_returns_409_without_rerunning_coordinator(
    client, fake_client
):
    session_id = _start_session(client)
    _send_user_turns(client, fake_client, session_id, count=3)

    # Force the session into 'grading' directly (simulating a first POST
    # .../end whose background task hasn't completed yet) rather than racing
    # a real background task from this single-threaded TestClient.
    db.mark_session_grading(session_id)

    resp = client.post(f"/practice/sessions/{session_id}/end")

    assert resp.status_code == 409
    detail = resp.json()["detail"]
    assert detail["report_url"] == f"/practice/sessions/{session_id}/report"

    # No coordinator call was made by this rejected second request.
    assert fake_client.sessions_create_calls == []
    assert fake_client.memories_create_calls == []


def test_end_called_twice_on_already_ended_session_returns_409_and_does_not_regrade(
    client, fake_client
):
    session_id = _start_session(client)
    _send_user_turns(client, fake_client, session_id, count=3)

    report_payload = {"scores": {"warmth": 3}, "focus_areas": ["Ask more questions"]}
    fake_client.queue_session_events(
        [agent_message_event(json.dumps(report_payload)), idle_event()]
    )
    first = client.post(f"/practice/sessions/{session_id}/end")
    assert first.status_code == 202

    # TestClient runs the BackgroundTask synchronously within the request
    # above, so grading has already completed and the session is 'ended' by
    # the time we get here.
    row = db.get_practice_session(session_id)
    assert row["status"] == "ended"
    assert len(fake_client.sessions_create_calls) == 1
    assert len(fake_client.memories_create_calls) == 1

    second = client.post(f"/practice/sessions/{session_id}/end")

    assert second.status_code == 409
    detail = second.json()["detail"]
    assert detail["report_url"] == f"/practice/sessions/{session_id}/report"

    # Crucially: the coordinator was NOT invoked again, and the report/
    # memory-store write was NOT repeated.
    assert len(fake_client.sessions_create_calls) == 1
    assert len(fake_client.memories_create_calls) == 1

    # And the saved report is untouched.
    report_resp = client.get(f"/practice/sessions/{session_id}/report", params={"user_id": "turns-user"})
    assert report_resp.json()["status"] == "ready"
    assert report_resp.json()["report"]["scores"] == {"warmth": 3}


# --- failure -> failed -> retry ---------------------------------------------


def test_background_failure_marks_failed_and_allows_retry_to_succeed(client, fake_client):
    session_id = _start_session(client)
    _send_user_turns(client, fake_client, session_id, count=3)

    # Simulate the coordinator blowing up: client.beta.sessions.create(...)
    # (the first CMA call inside coach.run_coaching_session) raises.
    fake_client.queue_session_create(RuntimeError("boom: leaked internal stack trace, api key, etc"))

    first = client.post(f"/practice/sessions/{session_id}/end")
    assert first.status_code == 202
    assert first.json() == {"status": "grading"}

    # TestClient ran the BackgroundTask synchronously -- it has already
    # failed and recorded status='failed' by the time we check.
    row = db.get_practice_session(session_id)
    assert row["status"] == "failed"
    assert len(fake_client.sessions_create_calls) == 1
    assert len(fake_client.memories_create_calls) == 0  # never reached on failure

    report_resp = client.get(f"/practice/sessions/{session_id}/report", params={"user_id": "turns-user"})
    assert report_resp.status_code == 200
    body = report_resp.json()
    assert body["status"] == "failed"
    assert body["report"] is None
    # The client-facing error must be a short, safe hint -- never the raw
    # exception text (which could carry internal/sensitive detail).
    assert body["error"] is not None
    assert "boom" not in body["error"]
    assert "api key" not in body["error"]

    # Retry: a fresh POST .../end on a 'failed' session must be allowed (not
    # blocked by the 409 rule that blocks grading/ended), and can succeed.
    report_payload = {"scores": {"warmth": 4}, "focus_areas": ["Slow down before topic changes"]}
    fake_client.queue_session_events(
        [agent_message_event(json.dumps(report_payload)), idle_event()]
    )
    retry = client.post(f"/practice/sessions/{session_id}/end")

    assert retry.status_code == 202
    assert retry.json() == {"status": "grading"}

    row_after_retry = db.get_practice_session(session_id)
    assert row_after_retry["status"] == "ended"
    assert row_after_retry["report_error"] is None  # cleared on the successful retry

    # The retry made a *second* coordinator session-create call and, this
    # time, a single memory-store write (not doubled from the failed attempt).
    assert len(fake_client.sessions_create_calls) == 2
    assert len(fake_client.memories_create_calls) == 1

    report_resp2 = client.get(f"/practice/sessions/{session_id}/report", params={"user_id": "turns-user"})
    body2 = report_resp2.json()
    assert body2["status"] == "ready"
    assert body2["report"]["scores"] == {"warmth": 4}
    assert body2["report"]["focus_areas"] == ["Slow down before topic changes"]


# --- GET .../report on an unknown session -----------------------------------


def test_get_report_for_unknown_session_returns_404(client):
    resp = client.get("/practice/sessions/nonexistent-session/report", params={"user_id": "anyone"})
    assert resp.status_code == 404


def test_get_report_before_end_is_called_reflects_active_status(client, fake_client):
    session_id = _start_session(client)

    resp = client.get(f"/practice/sessions/{session_id}/report", params={"user_id": "turns-user"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "active"
    assert body["report"] is None
