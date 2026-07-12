"""Parses the actual `text/event-stream` body of POST .../message to confirm
the SSE framing: one `data: {"delta": ...}` event per streamed chunk,
followed by a final `data: {"done": true}` event — see main.py's
`event_stream()` generator and partner.py's `stream_partner_reply`."""

import json

from app import db
from fake_anthropic import agent_message_event, idle_event


def _parse_sse(body: str) -> list[dict]:
    events = []
    for line in body.splitlines():
        line = line.strip()
        if not line or not line.startswith("data:"):
            continue
        payload = line[len("data:") :].strip()
        events.append(json.loads(payload))
    return events


def _start_session(client, user_id="sse-user", scenario_id="networking-mixer") -> str:
    resp = client.post("/practice/sessions", json={"user_id": user_id, "scenario_id": scenario_id})
    assert resp.status_code == 200
    return resp.json()["session_id"]


def test_message_emits_delta_events_then_done(client, fake_client):
    session_id = _start_session(client)

    fake_client.queue_message_stream(["Nice", " to", " meet you."])
    resp = client.post(f"/practice/sessions/{session_id}/message", json={"text": "Hi there"})
    assert resp.status_code == 200

    events = _parse_sse(resp.text)
    assert events == [
        {"delta": "Nice"},
        {"delta": " to"},
        {"delta": " meet you."},
        {"done": True},
    ]


def test_message_stream_persists_full_assistant_turn_to_transcript(client, fake_client):
    session_id = _start_session(client)

    # Two filler turns first so the session clears the 3-user-turn minimum
    # required before POST .../end will accept it (see main.py's
    # MIN_USER_TURNS_TO_GRADE) — the assertions below only care about the
    # "Go on" / "Part one. Part two." turn specifically, as a substring of
    # the full transcript text sent to the coordinator.
    fake_client.queue_message_stream(["ok"])
    client.post(f"/practice/sessions/{session_id}/message", json={"text": "Hi"})
    fake_client.queue_message_stream(["sure"])
    client.post(f"/practice/sessions/{session_id}/message", json={"text": "Tell me more"})

    fake_client.queue_message_stream(["Part one.", " Part two."])
    client.post(f"/practice/sessions/{session_id}/message", json={"text": "Go on"})

    # Confirm the assembled reply was appended as a single assistant turn by
    # ending the session and checking the transcript indirectly through the
    # coordinator call it triggers.
    fake_client.queue_session_events(
        [agent_message_event(json.dumps({"scores": {}, "focus_areas": []})), idle_event()]
    )
    client.post(f"/practice/sessions/{session_id}/end")

    # coach.run_coaching_session sends the full transcript as text in the
    # user.message event it sends to the coordinator session.
    sent = fake_client.sessions_events_send_calls[-1]
    sent_text = sent["events"][0]["content"][0]["text"]
    assert "USER: Go on" in sent_text
    assert "ASSISTANT: Part one. Part two." in sent_text


def test_message_with_no_chunks_still_emits_done(client, fake_client):
    session_id = _start_session(client)

    fake_client.queue_message_stream([])
    resp = client.post(f"/practice/sessions/{session_id}/message", json={"text": "..."})

    events = _parse_sse(resp.text)
    assert events == [{"done": True}]


# --- T7: mid-stream failure -> `error` SSE event + transcript rollback -----
#
# Transcript-consistency policy (see main.py's `event_stream` and db.py's
# `remove_last_turn`): when `stream_partner_reply` raises partway through,
# the *entire failed attempt* is rolled back to a clean end-state -- the
# dangling user turn appended before streaming started is popped back off,
# so the transcript afterward is byte-for-byte identical to what it was
# before the failed POST .../message was ever made. This is what "consistent,
# retry-safe" means here: not "leave the user turn and mark it somehow", but
# "as if the failed call never happened", so a client retry (re-sending the
# exact same text) reproduces the normal single-user-turn-then-reply shape
# rather than ever producing two consecutive user turns.


def test_message_stream_failure_emits_error_event_not_done(client, fake_client):
    session_id = _start_session(client)

    # Two real deltas flush before the underlying stream errors -- proves
    # this is a genuine *mid*-stream failure (partial output already sent),
    # not merely a failure before the first chunk.
    fake_client.queue_message_stream(["Sure, ", "no proble-", RuntimeError("stream broke")])
    resp = client.post(f"/practice/sessions/{session_id}/message", json={"text": "Hi there"})
    assert resp.status_code == 200

    events = _parse_sse(resp.text)
    assert events[0] == {"delta": "Sure, "}
    assert events[1] == {"delta": "no proble-"}
    assert len(events) == 3

    final = events[2]
    assert set(final.keys()) == {"error"}
    assert isinstance(final["error"], str) and final["error"]
    # Safe-message philosophy (matches `_safe_error_message`): the raw
    # exception text must never leak to the client, only a short, generic,
    # type-named hint.
    assert "stream broke" not in final["error"]
    assert "RuntimeError" in final["error"]

    # No `done` event anywhere in the body -- the client must be able to
    # tell "the partner finished" apart from "the stream failed" purely by
    # which terminal event arrived.
    assert not any("done" in e for e in events)


def test_message_stream_failure_rolls_back_dangling_user_turn(client, fake_client):
    session_id = _start_session(client)

    fake_client.queue_message_stream(["Oops", RuntimeError("boom")])
    client.post(f"/practice/sessions/{session_id}/message", json={"text": "Hi there"})

    # Chosen end-state: the transcript is exactly as if the failed call had
    # never happened -- not a dangling lone user turn, not a placeholder
    # assistant turn, nothing.
    assert db.get_transcript(session_id) == []


def test_retry_after_stream_failure_produces_one_clean_turn_pair(client, fake_client):
    session_id = _start_session(client)

    fake_client.queue_message_stream(["Oops", RuntimeError("boom")])
    client.post(f"/practice/sessions/{session_id}/message", json={"text": "Hi there"})
    assert db.get_transcript(session_id) == []

    # Retry with the exact same text the client would resend after seeing
    # the `error` event -- this must succeed normally and must NOT produce
    # two consecutive user turns (the bug this task fixes).
    fake_client.queue_message_stream(["Hey, ", "nice to meet you."])
    resp = client.post(f"/practice/sessions/{session_id}/message", json={"text": "Hi there"})
    assert resp.status_code == 200

    events = _parse_sse(resp.text)
    assert events[-1] == {"done": True}
    assert not any("error" in e for e in events)

    assert db.get_transcript(session_id) == [
        {"role": "user", "text": "Hi there"},
        {"role": "assistant", "text": "Hey, nice to meet you."},
    ]


def test_message_stream_failure_after_prior_successful_turns_only_rolls_back_the_failed_one(
    client, fake_client
):
    """A failure on turn N must not disturb turns 1..N-1 -- only the
    dangling turn from the failed attempt itself is removed."""
    session_id = _start_session(client)

    fake_client.queue_message_stream(["ok"])
    client.post(f"/practice/sessions/{session_id}/message", json={"text": "Hi"})

    fake_client.queue_message_stream(["sure"])
    client.post(f"/practice/sessions/{session_id}/message", json={"text": "Tell me more"})

    before = db.get_transcript(session_id)
    assert before == [
        {"role": "user", "text": "Hi"},
        {"role": "assistant", "text": "ok"},
        {"role": "user", "text": "Tell me more"},
        {"role": "assistant", "text": "sure"},
    ]

    fake_client.queue_message_stream([RuntimeError("boom")])
    client.post(f"/practice/sessions/{session_id}/message", json={"text": "Go on"})

    assert db.get_transcript(session_id) == before
