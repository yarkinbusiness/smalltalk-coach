"""T12: GET /practice/sessions/{session_id} -- the full transcript +
scenario + report for the iOS session-detail/replay screen (see
SessionDetailView.swift). Covers the four contractual guarantees:

  1. The owning user_id gets back the real transcript, scenario, and report.
  2. A wrong user_id is rejected (404 -- see main.py's get_session_detail
     docstring for the 403-vs-404 reasoning) and the rejection response
     itself never leaks the transcript/report content.
  3. An unknown session_id also 404s, with the exact same body shape as the
     wrong-user_id case -- the two are deliberately indistinguishable.
  4. A session that hasn't been graded yet returns report: null without
     erroring (still 200).
"""

import app.db as db_module


def _seed_graded_session(
    session_id: str, user_id: str, scenario_id: str, turns: list[tuple[str, str]], report: dict
) -> None:
    db_module.create_practice_session(session_id, user_id, scenario_id)
    for role, text in turns:
        db_module.append_turn(session_id, role, text)
    db_module.save_report(session_id, report)


def test_owner_gets_full_transcript_scenario_and_report(client):
    report = {
        "scores": {"warmth": 4, "curiosity": 3, "reciprocity": 4, "flow": 5},
        "strengths": ["Picked up on the opener naturally."],
        "focus_areas": ["Ask one follow-up before switching topics."],
        "drill_suggestion": "Practice asking a single follow-up per topic.",
        "raw": None,
        "parse_error": False,
    }
    _seed_graded_session(
        "session-owned",
        "owner-user",
        "coffee-shop-line",
        [
            ("assistant", "Hey, haven't seen you in a while!"),
            ("user", "Oh hey, yeah it's been busy."),
        ],
        report,
    )

    resp = client.get("/practice/sessions/session-owned", params={"user_id": "owner-user"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["transcript"] == [
        {"role": "assistant", "text": "Hey, haven't seen you in a while!"},
        {"role": "user", "text": "Oh hey, yeah it's been busy."},
    ]
    assert body["scenario"]["id"] == "coffee-shop-line"
    assert body["report"] == report


def test_wrong_user_id_returns_404_without_leaking_transcript_or_report(client):
    report = {
        "scores": {"warmth": 1, "curiosity": 1, "reciprocity": 1, "flow": 1},
        "strengths": [],
        "focus_areas": ["A private focus area nobody else should see"],
        "drill_suggestion": "A private drill suggestion",
        "raw": None,
        "parse_error": False,
    }
    _seed_graded_session(
        "session-not-yours",
        "real-owner",
        "gym-regular",
        [("assistant", "A very private opening line nobody else should see")],
        report,
    )

    resp = client.get("/practice/sessions/session-not-yours", params={"user_id": "not-the-owner"})

    assert resp.status_code == 404
    # The check must be specific: not just "status code is right" but "the
    # response body, in full, carries none of the private content" -- a
    # 404/403 whose detail message echoed the transcript or report back
    # would still be a real leak even with the "correct" status code.
    raw_text = resp.text
    assert "private opening line" not in raw_text
    assert "private focus area" not in raw_text
    assert "private drill suggestion" not in raw_text
    assert resp.json() == {"detail": "Unknown session_id"}


def test_unknown_session_id_returns_404(client):
    resp = client.get("/practice/sessions/does-not-exist", params={"user_id": "anyone"})

    assert resp.status_code == 404
    assert resp.json() == {"detail": "Unknown session_id"}


def test_wrong_user_id_and_unknown_session_id_return_identical_404_shape(client):
    """Documents the 403-vs-404 decision directly: a session that exists but
    belongs to someone else must be indistinguishable, at the HTTP layer,
    from a session_id that was never real -- otherwise the response itself
    would leak which session_ids are valid to a caller who doesn't own
    them."""
    db_module.create_practice_session("session-belongs-to-someone", "someone-else", "coffee-shop-line")

    wrong_owner_resp = client.get(
        "/practice/sessions/session-belongs-to-someone", params={"user_id": "attacker"}
    )
    unknown_resp = client.get("/practice/sessions/totally-made-up-id", params={"user_id": "attacker"})

    assert wrong_owner_resp.status_code == unknown_resp.status_code == 404
    assert wrong_owner_resp.json() == unknown_resp.json()


def test_ungraded_session_returns_report_null_without_erroring(client):
    resp_start = client.post(
        "/practice/sessions", json={"user_id": "ungraded-user", "scenario_id": "networking-mixer"}
    )
    session_id = resp_start.json()["session_id"]

    resp = client.get(f"/practice/sessions/{session_id}", params={"user_id": "ungraded-user"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["report"] is None
    assert body["scenario"]["id"] == "networking-mixer"
    assert body["transcript"] == []


def test_missing_user_id_query_param_returns_422(client):
    resp = client.get("/practice/sessions/some-session")

    assert resp.status_code == 422
