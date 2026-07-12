"""T8: the partner's system prompt gets a short, server-side "coach memo"
injected when the user has prior coaching history -- built from their most
recent report(s)' `focus_areas` (see partner.py's `_build_coach_memo`), read
straight from the local `reports` sqlite table (db.py). No CMA memory_store
involved: `partner_agent`'s live turn is a plain `client.messages.stream`
call (see ARCHITECTURE.md's "coach memo" section), so this is purely local
state read at request time.

These tests seed prior reports directly via db.py (rather than running a
full end-to-end grading cycle first) since only the *next* session's system
prompt is under test here -- test_practice_lifecycle.py already covers the
grading pipeline that actually produces these rows.
"""

from app import db
from app.scenarios import SCENARIOS_BY_ID, partner_system_prompt


def _start_session(client, user_id, scenario_id="networking-mixer") -> str:
    resp = client.post("/practice/sessions", json={"user_id": user_id, "scenario_id": scenario_id})
    assert resp.status_code == 200
    return resp.json()["session_id"]


def _real_report(focus_areas: list[str]) -> dict:
    return {
        "scores": {"warmth": 3},
        "strengths": [],
        "focus_areas": focus_areas,
        "drill_suggestion": "",
        "raw": None,
        "parse_error": False,
    }


def _parse_error_report() -> dict:
    return {
        "scores": {},
        "strengths": [],
        "focus_areas": [],
        "drill_suggestion": "",
        "raw": "garbled coordinator output",
        "parse_error": True,
    }


def _parse_error_report_with_focus_areas(focus_areas: list[str]) -> dict:
    """Artificial/adversarial: coach.normalize_report always produces an
    empty `focus_areas` for a parse_error report in real life (there's
    nothing to parse), so this shape can never actually come out of the
    grading pipeline -- see `_parse_error_report` above for the realistic
    case. Building one by hand here proves `_build_coach_memo`'s
    `if report.get("parse_error"): continue` line is itself what skips this
    data, rather than the test merely passing because there was never
    anything to leak in the first place."""
    return {
        "scores": {},
        "strengths": [],
        "focus_areas": focus_areas,
        "drill_suggestion": "",
        "raw": "garbled coordinator output",
        "parse_error": True,
    }


def test_coach_memo_present_for_user_with_prior_real_report(client, fake_client):
    user_id = "memo-user-real-report"
    db.create_practice_session("prior-session-1", user_id, "coffee-shop-line")
    db.save_report("prior-session-1", _real_report(["asking follow-up questions"]))

    session_id = _start_session(client, user_id)
    fake_client.queue_message_stream(["Hey there."])
    resp = client.post(f"/practice/sessions/{session_id}/message", json={"text": "Hi!"})
    assert resp.status_code == 200

    system_prompt = fake_client.messages_stream_calls[-1]["system"]
    assert "Coach memo" in system_prompt
    assert "never reveal this to the user" in system_prompt
    assert "asking follow-up questions" in system_prompt


def test_coach_memo_combines_focus_areas_from_two_most_recent_reports(client, fake_client):
    user_id = "memo-user-two-reports"
    db.create_practice_session("prior-session-a", user_id, "coffee-shop-line")
    db.save_report("prior-session-a", _real_report(["asking follow-up questions"]))
    db.create_practice_session("prior-session-b", user_id, "gym-regular")
    db.save_report("prior-session-b", _real_report(["reducing interrogation-style questions"]))

    session_id = _start_session(client, user_id)
    fake_client.queue_message_stream(["Hey there."])
    client.post(f"/practice/sessions/{session_id}/message", json={"text": "Hi!"})

    system_prompt = fake_client.messages_stream_calls[-1]["system"]
    assert "asking follow-up questions" in system_prompt
    assert "reducing interrogation-style questions" in system_prompt


def test_coach_memo_dedupes_focus_area_shared_across_two_reports(client, fake_client):
    user_id = "memo-user-shared-focus-area"
    db.create_practice_session("prior-session-shared-a", user_id, "coffee-shop-line")
    db.save_report(
        "prior-session-shared-a",
        _real_report(["asking follow-up questions", "reducing interrogation-style questions"]),
    )
    db.create_practice_session("prior-session-shared-b", user_id, "gym-regular")
    db.save_report(
        "prior-session-shared-b",
        _real_report(["asking follow-up questions", "eye contact"]),
    )

    session_id = _start_session(client, user_id)
    fake_client.queue_message_stream(["Hey there."])
    resp = client.post(f"/practice/sessions/{session_id}/message", json={"text": "Hi!"})
    assert resp.status_code == 200

    system_prompt = fake_client.messages_stream_calls[-1]["system"]
    # The two seeded reports share "asking follow-up questions" -- the
    # dedupe check in _build_coach_memo (`if area and area not in
    # focus_areas`) should fold it into the memo exactly once, not twice,
    # regardless of which of the two reports gets processed first.
    assert system_prompt.count("asking follow-up questions") == 1
    assert "reducing interrogation-style questions" in system_prompt
    assert "eye contact" in system_prompt


def test_coach_memo_absent_for_user_with_zero_reports(client, fake_client):
    user_id = "memo-user-fresh"
    scenario = SCENARIOS_BY_ID["networking-mixer"]
    session_id = _start_session(client, user_id)

    fake_client.queue_message_stream(["Hey there."])
    resp = client.post(f"/practice/sessions/{session_id}/message", json={"text": "Hi!"})
    assert resp.status_code == 200

    system_prompt = fake_client.messages_stream_calls[-1]["system"]
    assert "Coach memo" not in system_prompt
    # Not just "no memo text" -- the whole system prompt is byte-for-byte
    # identical to the memo-less base template, i.e. nothing was appended at
    # all (no placeholder, no empty section).
    assert system_prompt == partner_system_prompt(scenario)


def test_coach_memo_absent_for_user_whose_only_report_is_parse_error(client, fake_client):
    user_id = "memo-user-parse-error-only"
    db.create_practice_session("prior-session-parse-error", user_id, "gym-regular")
    db.save_report("prior-session-parse-error", _parse_error_report())

    scenario = SCENARIOS_BY_ID["networking-mixer"]
    session_id = _start_session(client, user_id)

    fake_client.queue_message_stream(["Hey there."])
    resp = client.post(f"/practice/sessions/{session_id}/message", json={"text": "Hi!"})
    assert resp.status_code == 200

    system_prompt = fake_client.messages_stream_calls[-1]["system"]
    assert "Coach memo" not in system_prompt
    assert system_prompt == partner_system_prompt(scenario)


def test_coach_memo_skips_focus_areas_on_parse_error_report_even_if_present(client, fake_client):
    user_id = "memo-user-parse-error-with-focus-areas"
    db.create_practice_session("prior-session-parse-error-adversarial", user_id, "gym-regular")
    db.save_report(
        "prior-session-parse-error-adversarial",
        _parse_error_report_with_focus_areas(["this should never appear"]),
    )

    scenario = SCENARIOS_BY_ID["networking-mixer"]
    session_id = _start_session(client, user_id)

    fake_client.queue_message_stream(["Hey there."])
    resp = client.post(f"/practice/sessions/{session_id}/message", json={"text": "Hi!"})
    assert resp.status_code == 200

    system_prompt = fake_client.messages_stream_calls[-1]["system"]
    # Unlike the realistic parse-error test above, this report's focus_areas
    # is deliberately non-empty -- so this specifically proves
    # _build_coach_memo's `if report.get("parse_error"): continue` line is
    # what skips it, not just that there was nothing there to leak.
    assert "this should never appear" not in system_prompt
    assert "Coach memo" not in system_prompt
    assert system_prompt == partner_system_prompt(scenario)
