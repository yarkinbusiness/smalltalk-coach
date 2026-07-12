"""T10: GET /users/{user_id}/recommendation -- proves the route is actually
wired to real db-backed history (app.db.create_practice_session /
app.db.save_report), on top of test_recommend.py's pure-function coverage
of the algorithm itself against hand-built histories.
"""

import app.db as db_module


def _seed_report(user_id: str, scenario_id: str, report: dict, *, session_id: str) -> None:
    db_module.create_practice_session(session_id, user_id, scenario_id)
    db_module.save_report(session_id, report)


def test_recommendation_for_brand_new_user_is_easiest_scenario(client):
    resp = client.get("/users/brand-new-user/recommendation")
    assert resp.status_code == 200

    body = resp.json()
    assert body["scenario_id"] == "coffee-shop-line"
    assert "start here" in body["reason"].lower()


def test_recommendation_reflects_real_saved_reports(client):
    """Seeds two real practice_sessions + reports rows (via the same
    db.py functions main.py itself uses) showing reciprocity as the
    unambiguous recurring weak dimension, then hits the real HTTP route --
    confirming GET .../recommendation actually reads db.get_progress and
    feeds it through recommend_next_scenario, not just that the pure
    function works in isolation."""
    user_id = "user-with-history"
    _seed_report(
        user_id,
        "networking-mixer",
        {
            "scores": {"warmth": 4, "curiosity": 4, "reciprocity": 2, "flow": 4},
            "strengths": [],
            "focus_areas": [],
            "drill_suggestion": "",
            "raw": None,
            "parse_error": False,
        },
        session_id="seed-session-1",
    )
    _seed_report(
        user_id,
        "elevator-coworker",
        {
            "scores": {"warmth": 3, "curiosity": 4, "reciprocity": 1, "flow": 4},
            "strengths": [],
            "focus_areas": [],
            "drill_suggestion": "",
            "raw": None,
            "parse_error": False,
        },
        session_id="seed-session-2",
    )

    resp = client.get(f"/users/{user_id}/recommendation")
    assert resp.status_code == 200

    body = resp.json()
    assert body["scenario_id"] == "dinner-party-stranger"
    assert "reciprocity" in body["reason"].lower()


def test_recommendation_ignores_parse_error_reports_end_to_end(client):
    """A user whose only saved report is a parse_error should be treated
    exactly like a brand new user by the real route -- proving the
    exclusion holds through the actual db round-trip, not just in memory."""
    user_id = "user-only-parse-errors"
    _seed_report(
        user_id,
        "networking-mixer",
        {
            "scores": {},
            "strengths": [],
            "focus_areas": [],
            "drill_suggestion": "",
            "raw": "unparseable garbage",
            "parse_error": True,
        },
        session_id="seed-session-parse-error",
    )

    resp = client.get(f"/users/{user_id}/recommendation")
    assert resp.status_code == 200

    body = resp.json()
    assert body["scenario_id"] == "coffee-shop-line"
    assert "start here" in body["reason"].lower()
