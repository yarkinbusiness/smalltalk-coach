"""Ownership guard on GET /practice/sessions/{session_id}/report.

An independent review found this route had no ownership check at all --
anyone who knew or guessed a session_id could read that session's full
coaching report (scores, focus_areas, drill_suggestion) regardless of whose
session it was. This mirrors the fix already applied to the sibling route
GET /practice/sessions/{session_id} (see test_session_detail_endpoint.py /
main.py's `get_session_detail` docstring for the full 403-vs-404 reasoning):
a required `user_id` query parameter that must match the session's actual
owner, with a plain 404 -- identical status and body for "wrong owner" and
"session doesn't exist" -- so an unauthorized caller can't tell the two
apart.

Covers all four `status` values GET .../report can report
(active/grading/ready/failed): the owner must see real data in every one of
them, and a non-owner must be rejected before any of that data is ever
computed, regardless of which state the session is in.
"""

import app.db as db_module


def _seed_ready_session(
    session_id: str, user_id: str, scenario_id: str, report: dict
) -> None:
    db_module.create_practice_session(session_id, user_id, scenario_id)
    db_module.save_report(session_id, report)
    db_module.mark_session_grading(session_id)
    db_module.mark_session_ended(session_id)


# --- owner: all four states still work exactly as before --------------------


def test_owner_gets_ready_report(client):
    report = {
        "scores": {"warmth": 4, "curiosity": 3, "reciprocity": 4, "flow": 5},
        "strengths": ["Picked up on the opener naturally."],
        "focus_areas": ["Ask one follow-up before switching topics."],
        "drill_suggestion": "Practice asking a single follow-up per topic.",
        "raw": None,
        "parse_error": False,
    }
    _seed_ready_session("session-ready", "owner-user", "coffee-shop-line", report)

    resp = client.get("/practice/sessions/session-ready/report", params={"user_id": "owner-user"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ready"
    assert body["report"] == report
    assert body["error"] is None


def test_owner_gets_active_report(client):
    db_module.create_practice_session("session-active", "owner-user", "coffee-shop-line")

    resp = client.get("/practice/sessions/session-active/report", params={"user_id": "owner-user"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "active"
    assert body["report"] is None


def test_owner_gets_grading_report(client):
    db_module.create_practice_session("session-grading", "owner-user", "coffee-shop-line")
    db_module.mark_session_grading("session-grading")

    resp = client.get("/practice/sessions/session-grading/report", params={"user_id": "owner-user"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "grading"
    assert body["report"] is None


def test_owner_gets_failed_report(client):
    db_module.create_practice_session("session-failed", "owner-user", "coffee-shop-line")
    db_module.mark_session_grading("session-failed")
    db_module.mark_session_failed("session-failed", "Grading failed (RuntimeError). You can retry.")

    resp = client.get("/practice/sessions/session-failed/report", params={"user_id": "owner-user"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "failed"
    assert body["report"] is None
    assert body["error"] == "Grading failed (RuntimeError). You can retry."


# --- wrong owner / unknown session: identical, non-leaking 404 --------------


def test_wrong_user_id_returns_404_without_leaking_report_data(client):
    report = {
        "scores": {"warmth": 1, "curiosity": 1, "reciprocity": 1, "flow": 1},
        "strengths": [],
        "focus_areas": ["A private focus area nobody else should see"],
        "drill_suggestion": "A private drill suggestion",
        "raw": None,
        "parse_error": False,
    }
    _seed_ready_session("session-not-yours", "real-owner", "gym-regular", report)

    resp = client.get(
        "/practice/sessions/session-not-yours/report", params={"user_id": "not-the-owner"}
    )

    assert resp.status_code == 404
    raw_text = resp.text
    assert "private focus area" not in raw_text
    assert "private drill suggestion" not in raw_text
    assert "warmth" not in raw_text
    assert resp.json() == {"detail": "Unknown session_id"}


def test_wrong_user_id_on_failed_session_does_not_leak_error_detail(client):
    db_module.create_practice_session("session-failed-private", "real-owner", "coffee-shop-line")
    db_module.mark_session_grading("session-failed-private")
    db_module.mark_session_failed(
        "session-failed-private", "some retryable, still-somewhat-sensitive hint"
    )

    resp = client.get(
        "/practice/sessions/session-failed-private/report", params={"user_id": "attacker"}
    )

    assert resp.status_code == 404
    assert "retryable" not in resp.text
    assert resp.json() == {"detail": "Unknown session_id"}


def test_unknown_session_id_returns_404(client):
    resp = client.get("/practice/sessions/does-not-exist/report", params={"user_id": "anyone"})

    assert resp.status_code == 404
    assert resp.json() == {"detail": "Unknown session_id"}


def test_wrong_user_id_and_unknown_session_id_return_byte_identical_404(client):
    """The entire point of this fix: a session that exists but belongs to
    someone else must be indistinguishable, at the HTTP layer -- same status
    code, same response body, byte for byte -- from a session_id that was
    never real. Any difference here (a different detail string, an extra
    field, different whitespace) would let an attacker enumerate valid
    session_ids just by diffing responses."""
    report = {
        "scores": {"warmth": 5, "curiosity": 5, "reciprocity": 5, "flow": 5},
        "strengths": ["s"],
        "focus_areas": ["f"],
        "drill_suggestion": "d",
        "raw": None,
        "parse_error": False,
    }
    _seed_ready_session("session-belongs-to-someone", "someone-else", "coffee-shop-line", report)

    wrong_owner_resp = client.get(
        "/practice/sessions/session-belongs-to-someone/report", params={"user_id": "attacker"}
    )
    unknown_resp = client.get(
        "/practice/sessions/totally-made-up-id/report", params={"user_id": "attacker"}
    )

    assert wrong_owner_resp.status_code == unknown_resp.status_code == 404
    assert wrong_owner_resp.content == unknown_resp.content
    assert wrong_owner_resp.headers["content-type"] == unknown_resp.headers["content-type"]
    assert wrong_owner_resp.json() == unknown_resp.json()


def test_wrong_user_id_on_active_session_returns_404(client):
    """Not just ready/failed sessions -- an in-progress (active) session
    must be equally invisible to a non-owner probing its status."""
    db_module.create_practice_session("session-active-private", "real-owner", "coffee-shop-line")

    resp = client.get(
        "/practice/sessions/session-active-private/report", params={"user_id": "attacker"}
    )

    assert resp.status_code == 404
    assert resp.json() == {"detail": "Unknown session_id"}


def test_wrong_user_id_on_grading_session_returns_404(client):
    db_module.create_practice_session("session-grading-private", "real-owner", "coffee-shop-line")
    db_module.mark_session_grading("session-grading-private")

    resp = client.get(
        "/practice/sessions/session-grading-private/report", params={"user_id": "attacker"}
    )

    assert resp.status_code == 404
    assert resp.json() == {"detail": "Unknown session_id"}


def test_missing_user_id_query_param_returns_422(client):
    resp = client.get("/practice/sessions/some-session/report")

    assert resp.status_code == 422
