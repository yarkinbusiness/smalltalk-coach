"""T11: GET /users/{user_id}/progress/summary -- proves the route is
actually wired to real db-backed history (app.db.create_practice_session /
app.db.save_report), on top of test_progress_summary.py's pure-function
coverage of build_progress_summary itself against hand-built histories.
"""

import app.db as db_module


def _seed_report(user_id: str, scenario_id: str, report: dict, *, session_id: str) -> None:
    db_module.create_practice_session(session_id, user_id, scenario_id)
    db_module.save_report(session_id, report)


def test_summary_for_brand_new_user_is_a_graceful_empty_shape(client):
    """No sessions at all -- must be a 200 with a sensible zero shape, not
    a 404/500."""
    resp = client.get("/users/brand-new-user/progress/summary")
    assert resp.status_code == 200

    body = resp.json()
    assert body["session_count"] == 0
    assert body["current_focus_area"] is None
    assert body["dimensions"] == {
        "warmth": [],
        "curiosity": [],
        "reciprocity": [],
        "flow": [],
    }


def test_summary_reflects_real_saved_reports_in_chronological_order(client):
    """Seeds three real practice_sessions + reports rows (via the same
    db.py functions main.py itself uses), each with a distinct,
    increasing warmth score, then hits the real HTTP route -- confirming
    GET .../progress/summary actually reads db.get_progress (which orders
    by created_at ASC) and not some other/reversed ordering."""
    user_id = "user-with-history"
    _seed_report(
        user_id,
        "networking-mixer",
        {
            "scores": {"warmth": 2, "curiosity": 2, "reciprocity": 2, "flow": 2},
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
            "scores": {"warmth": 3, "curiosity": 3, "reciprocity": 3, "flow": 3},
            "strengths": [],
            "focus_areas": [],
            "drill_suggestion": "",
            "raw": None,
            "parse_error": False,
        },
        session_id="seed-session-2",
    )
    _seed_report(
        user_id,
        "coffee-shop-line",
        {
            "scores": {"warmth": 4, "curiosity": 4, "reciprocity": 4, "flow": 4},
            "strengths": [],
            "focus_areas": [],
            "drill_suggestion": "",
            "raw": None,
            "parse_error": False,
        },
        session_id="seed-session-3",
    )

    resp = client.get(f"/users/{user_id}/progress/summary")
    assert resp.status_code == 200

    body = resp.json()
    assert body["session_count"] == 3
    assert [p["score"] for p in body["dimensions"]["warmth"]] == [2, 3, 4]
    assert [p["session_index"] for p in body["dimensions"]["warmth"]] == [0, 1, 2]


def test_summary_skips_parse_error_session_sandwiched_between_real_ones(client):
    """The critical case: a parse_error session saved *between* two real,
    scored sessions (by created_at). The route must return a 2-point
    series, not 3 with a fake/zero middle point, proving the exclusion
    holds through the actual db round-trip and not just in memory."""
    user_id = "user-with-a-parse-error-in-the-middle"
    _seed_report(
        user_id,
        "networking-mixer",
        {
            "scores": {"warmth": 5, "curiosity": 5, "reciprocity": 5, "flow": 5},
            "strengths": [],
            "focus_areas": [],
            "drill_suggestion": "",
            "raw": None,
            "parse_error": False,
        },
        session_id="seed-session-real-1",
    )
    _seed_report(
        user_id,
        "elevator-coworker",
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
    _seed_report(
        user_id,
        "coffee-shop-line",
        {
            "scores": {"warmth": 1, "curiosity": 1, "reciprocity": 1, "flow": 1},
            "strengths": [],
            "focus_areas": [],
            "drill_suggestion": "",
            "raw": None,
            "parse_error": False,
        },
        session_id="seed-session-real-2",
    )

    resp = client.get(f"/users/{user_id}/progress/summary")
    assert resp.status_code == 200

    body = resp.json()
    assert body["session_count"] == 2  # not 3
    for dim in ("warmth", "curiosity", "reciprocity", "flow"):
        series = body["dimensions"][dim]
        assert len(series) == 2  # not 3
        assert [p["session_index"] for p in series] == [0, 1]  # adjacent, no gap
        assert [p["score"] for p in series] == [5, 1]


def test_summary_current_focus_area_matches_recommendation_endpoint(client):
    """Seeds the same recurring-reciprocity-weakness history used in
    test_recommend_endpoint.test_recommendation_reflects_real_saved_reports,
    then checks that GET .../progress/summary's current_focus_area agrees
    with what GET .../recommendation would act on for the same user --
    both should read reciprocity as the shared weak-dimension signal."""
    user_id = "user-with-reciprocity-weakness"
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

    resp = client.get(f"/users/{user_id}/progress/summary")
    assert resp.status_code == 200
    assert resp.json()["current_focus_area"] == "reciprocity"

    rec_resp = client.get(f"/users/{user_id}/recommendation")
    assert "reciprocity" in rec_resp.json()["reason"].lower()
