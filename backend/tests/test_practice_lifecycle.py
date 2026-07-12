"""End-to-end practice-session lifecycle through the real FastAPI routes:
POST /practice/sessions -> POST .../message -> POST .../end -> GET progress.

Runs against a temp sqlite DB (see conftest.client fixture) and FakeAnthropic
(no real network calls) — but exercises the actual routing/dependency
wiring, db.py, coach.py, memory.py, partner.py logic, not isolated units.
"""

import json

from fake_anthropic import agent_message_event, idle_event


def test_full_practice_lifecycle(client, fake_client):
    # 1. start a session
    start_resp = client.post(
        "/practice/sessions", json={"user_id": "user-1", "scenario_id": "coffee-shop-line"}
    )
    assert start_resp.status_code == 200
    start_body = start_resp.json()
    session_id = start_body["session_id"]
    assert start_body["scenario"]["id"] == "coffee-shop-line"

    # starting a session provisions a memory store for the user (idempotent
    # ensure_user_memory_store call) via the fake client, not the real API
    assert len(fake_client.memory_stores_create_calls) == 1

    # 2. send a message, partner streams a reply through the fake client
    fake_client.queue_message_stream(["Oh, hey!", " Small world."])
    msg_resp = client.post(
        f"/practice/sessions/{session_id}/message", json={"text": "Hi, small world huh?"}
    )
    assert msg_resp.status_code == 200
    assert msg_resp.headers["content-type"].startswith("text/event-stream")
    assert "Oh, hey!" in msg_resp.text

    # the partner call used the model pinned in the (fake) provisioned state
    assert fake_client.messages_stream_calls[-1]["model"] == "claude-sonnet-5"

    # send two more user turns so the session clears the 3-user-turn minimum
    # required before it can be ended and graded.
    fake_client.queue_message_stream(["Sure, "])
    client.post(f"/practice/sessions/{session_id}/message", json={"text": "What do you do?"})
    fake_client.queue_message_stream(["Nice."])
    client.post(f"/practice/sessions/{session_id}/message", json={"text": "That's cool."})

    # 3. end the session — coach.run_coaching_session drives a fake CMA
    # session that "thinks out loud" then emits the final report JSON. The
    # coaching run itself happens in a FastAPI BackgroundTask (see main.py's
    # end_practice/_run_coaching_task), so POST .../end returns 202 with just
    # {"status": "grading"} — the report is fetched separately via GET
    # .../report once grading completes.
    report_payload = {
        "scores": {"warmth": 4, "curiosity": 3, "reciprocity": 4, "flow": 5},
        "strengths": ["Picked up on the 'small world' opening naturally."],
        "focus_areas": ["Ask one follow-up before switching topics."],
        "drill_suggestion": "Practice asking a single follow-up question per topic.",
    }
    fake_client.queue_session_events(
        [
            agent_message_event("Let me review the transcript first..."),
            agent_message_event(json.dumps(report_payload)),
            idle_event(),
        ]
    )
    # coach.normalize_report runs on the coordinator's raw output before it's
    # saved, so the eventual report is the full CoachReport shape: the four
    # business fields unchanged (this payload is already well-formed) plus
    # the always-present raw/parse_error fields (None/False on the success
    # path — see coach.normalize_report's docstring for the full policy).
    expected_report = {**report_payload, "raw": None, "parse_error": False}
    end_resp = client.post(f"/practice/sessions/{session_id}/end")
    assert end_resp.status_code == 202
    assert end_resp.json() == {"status": "grading"}

    # FastAPI TestClient runs BackgroundTasks synchronously within the
    # request/response cycle (see test_end_session_async.py for the test
    # that proves the *real* early-return timing guarantee against a live
    # server) — so by the time .post() above returned, grading has already
    # finished here, and GET .../report reflects the completed report.
    report_resp = client.get(f"/practice/sessions/{session_id}/report", params={"user_id": "user-1"})
    assert report_resp.status_code == 200
    report_body = report_resp.json()
    assert report_body["status"] == "ready"
    assert report_body["report"] == expected_report

    # the coordinator session was created against the pinned coordinator id
    create_call = fake_client.sessions_create_calls[-1]
    assert create_call["agent"] == {"type": "agent", "id": "agent-coordinator", "version": 1}
    assert create_call["environment_id"] == "env-test"

    # record_session_summary wrote the report back into the (fake) memory store
    assert len(fake_client.memories_create_calls) == 1
    assert fake_client.memories_create_calls[0]["path"] == f"/sessions/{session_id}.md"

    # 4. progress now reflects the ended session
    progress_resp = client.get("/users/user-1/progress")
    assert progress_resp.status_code == 200
    progress = progress_resp.json()
    assert len(progress) == 1
    assert progress[0]["session_id"] == session_id
    assert progress[0]["scenario_id"] == "coffee-shop-line"
    assert progress[0]["report"] == expected_report


def test_start_practice_unknown_scenario_returns_404(client):
    resp = client.post(
        "/practice/sessions", json={"user_id": "user-2", "scenario_id": "does-not-exist"}
    )
    assert resp.status_code == 404


def test_message_to_unknown_session_returns_404(client):
    resp = client.post("/practice/sessions/nonexistent-session/message", json={"text": "hi"})
    assert resp.status_code == 404


def test_end_unknown_session_returns_404(client):
    resp = client.post("/practice/sessions/nonexistent-session/end")
    assert resp.status_code == 404


def test_message_after_session_ended_returns_409(client, fake_client):
    start_resp = client.post(
        "/practice/sessions", json={"user_id": "user-3", "scenario_id": "gym-regular"}
    )
    session_id = start_resp.json()["session_id"]

    # 3 user turns to clear the minimum-turns guard on POST .../end below.
    for text in ["hey", "how's it going", "nice to meet you"]:
        fake_client.queue_message_stream(["Sure."])
        client.post(f"/practice/sessions/{session_id}/message", json={"text": text})

    fake_client.queue_session_events(
        [agent_message_event(json.dumps({"scores": {}, "focus_areas": []})), idle_event()]
    )
    client.post(f"/practice/sessions/{session_id}/end")

    resp = client.post(f"/practice/sessions/{session_id}/message", json={"text": "still there?"})
    assert resp.status_code == 409


def test_bootstrap_user_creates_memory_store(client, fake_client):
    resp = client.post("/users/user-4/bootstrap")
    assert resp.status_code == 200
    body = resp.json()
    assert body["user_id"] == "user-4"
    assert body["memory_store_id"]
    assert len(fake_client.memory_stores_create_calls) == 1

    # calling again is idempotent — no second CMA create call, same id
    resp2 = client.post("/users/user-4/bootstrap")
    assert resp2.json()["memory_store_id"] == body["memory_store_id"]
    assert len(fake_client.memory_stores_create_calls) == 1
