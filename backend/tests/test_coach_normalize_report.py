"""coach.normalize_report — coercing whatever _extract_report produced into
a shape that reliably satisfies the CoachReport pydantic model (schemas.py),
without ever raising, no matter how malformed the input is.

See coach.normalize_report's docstring for the full normalization policy;
these tests pin down the concrete cases called out there:

  - scores: float / numeric-string / out-of-range values coerced+clamped to
    an int in [1, 5]; a missing dimension key is *omitted* (not
    defaulted); non-numeric garbage is also omitted; an unexpected extra
    key in `scores` is dropped.
  - strengths / focus_areas: coerced to list[str]; a bare string becomes a
    single-item list; other non-list/non-string garbage becomes [].
  - drill_suggestion: coerced with str().
  - a fundamentally unparseable input (not a dict, missing scores/
    focus_areas entirely, or already an _extract_report parse_error
    fallback) degrades cleanly to the canonical parse_error shape.
  - a well-formed input passes through unchanged (plus raw=None,
    parse_error=False).

The last section also drives the full POST /end route (via the fake
Anthropic client) with a malformed coordinator payload, confirming the
route as a whole never 500s and always returns something CoachReport-valid.
"""

import json

import pytest
from pydantic import ValidationError

from app import coach
from app.schemas import CoachReport
from fake_anthropic import agent_message_event, idle_event


# --- scores: numeric coercion + clamping ------------------------------------


def test_normalize_report_coerces_float_scores():
    raw = {
        "scores": {"warmth": 4.5, "curiosity": 2.2, "reciprocity": 3.0, "flow": 4.9},
        "focus_areas": [],
    }

    result = coach.normalize_report(raw)

    # 4.5 rounds half-to-even (Python's round()) -> 4; the rest round normally.
    assert result["scores"] == {"warmth": 4, "curiosity": 2, "reciprocity": 3, "flow": 5}
    assert all(isinstance(v, int) for v in result["scores"].values())
    assert result["parse_error"] is False


def test_normalize_report_coerces_numeric_string_scores():
    raw = {"scores": {"warmth": "4", "curiosity": " 3 ", "reciprocity": "2.6"}, "focus_areas": []}

    result = coach.normalize_report(raw)

    assert result["scores"] == {"warmth": 4, "curiosity": 3, "reciprocity": 3}


@pytest.mark.parametrize(
    "value, expected",
    [(0, 1), (-1, 1), (-100, 1), (6, 5), (100, 5), (5, 5), (1, 1)],
)
def test_normalize_report_clamps_out_of_range_scores(value, expected):
    raw = {"scores": {"warmth": value}, "focus_areas": []}

    result = coach.normalize_report(raw)

    assert result["scores"] == {"warmth": expected}


def test_normalize_report_omits_non_numeric_garbage_score():
    """A dimension whose value can't be read as a number at all (not even a
    numeric string) is dropped from the output rather than defaulted or
    raising."""
    raw = {
        "scores": {"warmth": "n/a", "curiosity": None, "reciprocity": [1, 2], "flow": 4},
        "focus_areas": [],
    }

    result = coach.normalize_report(raw)

    assert result["scores"] == {"flow": 4}


def test_normalize_report_treats_bool_score_as_garbage_not_zero_or_one():
    # bool is a subclass of int in Python -- True/False must not silently
    # become scores of 1/0.
    raw = {"scores": {"warmth": True, "curiosity": False}, "focus_areas": []}

    result = coach.normalize_report(raw)

    assert result["scores"] == {}


# --- scores: missing / extra dimension keys ---------------------------------


def test_normalize_report_omits_missing_dimension_keys():
    """Policy: a dimension key absent from the input is simply left out of
    the output -- never defaulted to a sentinel score."""
    raw = {"scores": {"warmth": 4, "curiosity": 3}, "focus_areas": []}

    result = coach.normalize_report(raw)

    assert result["scores"] == {"warmth": 4, "curiosity": 3}
    assert "reciprocity" not in result["scores"]
    assert "flow" not in result["scores"]


def test_normalize_report_drops_unexpected_extra_score_key():
    """Policy: an extra key in `scores` that isn't one of the four known
    dimensions is silently dropped, not preserved or rejected."""
    raw = {
        "scores": {"warmth": 4, "curiosity": 3, "reciprocity": 4, "flow": 5, "tone": 5, "vibes": "great"},
        "focus_areas": [],
    }

    result = coach.normalize_report(raw)

    assert result["scores"] == {"warmth": 4, "curiosity": 3, "reciprocity": 4, "flow": 5}


def test_normalize_report_handles_non_dict_scores_container():
    """If `scores` itself isn't even a dict (e.g. the coordinator emitted a
    string or list there), normalize_report yields no scores rather than
    raising."""
    raw = {"scores": "not a dict", "focus_areas": []}

    result = coach.normalize_report(raw)

    assert result["scores"] == {}


# --- strengths / focus_areas: list[str] coercion ----------------------------


def test_normalize_report_wraps_bare_string_strengths_in_a_list():
    raw = {
        "scores": {},
        "strengths": "Great eye contact throughout.",
        "focus_areas": ["Ask more follow-ups"],
    }

    result = coach.normalize_report(raw)

    assert result["strengths"] == ["Great eye contact throughout."]


def test_normalize_report_wraps_bare_string_focus_areas_in_a_list():
    raw = {"scores": {}, "focus_areas": "Slow down between topics."}

    result = coach.normalize_report(raw)

    assert result["focus_areas"] == ["Slow down between topics."]


@pytest.mark.parametrize("garbage", [None, 42, {"a": "b"}, 3.14])
def test_normalize_report_non_list_non_string_strengths_becomes_empty_list(garbage):
    raw = {"scores": {}, "strengths": garbage, "focus_areas": []}

    result = coach.normalize_report(raw)

    assert result["strengths"] == []


def test_normalize_report_stringifies_non_string_list_items_and_drops_nones():
    raw = {"scores": {}, "strengths": ["ok", 5, None, True], "focus_areas": []}

    result = coach.normalize_report(raw)

    assert result["strengths"] == ["ok", "5", "True"]


# --- drill_suggestion --------------------------------------------------------


def test_normalize_report_coerces_drill_suggestion_to_str():
    raw = {"scores": {}, "focus_areas": [], "drill_suggestion": 12345}

    result = coach.normalize_report(raw)

    assert result["drill_suggestion"] == "12345"


def test_normalize_report_missing_drill_suggestion_defaults_to_empty_string():
    raw = {"scores": {}, "focus_areas": []}

    result = coach.normalize_report(raw)

    assert result["drill_suggestion"] == ""


# --- fundamentally unparseable input -> parse_error fallback ----------------


def test_normalize_report_missing_scores_and_focus_areas_keys_degrades_to_parse_error():
    raw = {"strengths": ["irrelevant"]}

    result = coach.normalize_report(raw)

    assert result == {
        "scores": {},
        "strengths": [],
        "focus_areas": [],
        "drill_suggestion": "",
        "raw": "",
        "parse_error": True,
    }


def test_normalize_report_non_dict_input_degrades_to_parse_error():
    for garbage in [None, "just a string", 42, ["a", "list"]]:
        result = coach.normalize_report(garbage)
        assert result["parse_error"] is True
        assert result["scores"] == {}
        assert result["strengths"] == []
        assert result["focus_areas"] == []


def test_normalize_report_preserves_existing_parse_error_fallback():
    """Feeding normalize_report the exact fallback shape _extract_report
    itself produces (already parse_error) should be a no-op that carries the
    original raw text forward, not an attempt to re-parse it."""
    already_fallback = coach._extract_report(["not json at all", "{still not valid"])

    result = coach.normalize_report(already_fallback)

    assert result["parse_error"] is True
    assert result["raw"] == "{still not valid"
    assert result["scores"] == {}
    assert result["strengths"] == []
    assert result["focus_areas"] == []
    assert result["drill_suggestion"] == ""


def test_normalize_report_end_to_end_from_extract_report_garbage_messages():
    """The realistic pipeline: garbage agent messages -> _extract_report's
    fallback -> normalize_report -- confirm the whole chain degrades
    cleanly and CoachReport(**result) validates without raising."""
    extracted = coach._extract_report(["nonsense", "{broken json"])

    result = coach.normalize_report(extracted)

    assert result["parse_error"] is True
    CoachReport(**result)  # must not raise


# --- well-formed input passes through unchanged -----------------------------


def test_normalize_report_well_formed_input_passes_through():
    raw = {
        "scores": {"warmth": 4, "curiosity": 3, "reciprocity": 4, "flow": 5},
        "strengths": ["Picked up on the opening naturally."],
        "focus_areas": ["Ask one follow-up before switching topics."],
        "drill_suggestion": "Practice asking a single follow-up question per topic.",
    }

    result = coach.normalize_report(raw)

    assert result == {
        "scores": {"warmth": 4, "curiosity": 3, "reciprocity": 4, "flow": 5},
        "strengths": ["Picked up on the opening naturally."],
        "focus_areas": ["Ask one follow-up before switching topics."],
        "drill_suggestion": "Practice asking a single follow-up question per topic.",
        "raw": None,
        "parse_error": False,
    }
    # And it must satisfy the actual pydantic model, not just look right.
    CoachReport(**result)


def test_normalize_report_output_always_satisfies_coach_report_model():
    """Fuzz-ish sweep: every case above, run through the real CoachReport
    model constructor -- none of them should raise ValidationError."""
    cases = [
        {"scores": {"warmth": 4.5}, "focus_areas": []},
        {"scores": {"warmth": "4"}, "focus_areas": []},
        {"scores": {"warmth": 0, "curiosity": 6, "reciprocity": -1}, "focus_areas": []},
        {"scores": {"warmth": 4, "curiosity": 3}, "focus_areas": []},
        {"scores": {"warmth": 4, "tone": 5}, "focus_areas": []},
        {"scores": {}, "strengths": "single string", "focus_areas": []},
        {"foo": "bar"},
        None,
        "garbage",
        {
            "scores": {"warmth": 4, "curiosity": 3, "reciprocity": 4, "flow": 5},
            "strengths": ["good"],
            "focus_areas": ["better"],
            "drill_suggestion": "practice",
        },
    ]
    for raw in cases:
        normalized = coach.normalize_report(raw)
        try:
            CoachReport(**normalized)
        except ValidationError as exc:  # pragma: no cover - failure path
            pytest.fail(f"normalize_report({raw!r}) -> {normalized!r} failed CoachReport: {exc}")


# --- full /end route, through the fake Anthropic client --------------------


def test_end_route_with_malformed_coordinator_output_still_returns_clean_report(
    client, fake_client
):
    """Drives the real POST /end route with a coordinator payload that has
    float scores, an out-of-range score, and a missing dimension key --
    confirms the route doesn't 500 and returns an already-normalized,
    CoachReport-valid body."""
    start_resp = client.post(
        "/practice/sessions", json={"user_id": "user-malformed", "scenario_id": "coffee-shop-line"}
    )
    session_id = start_resp.json()["session_id"]

    # 3 user turns to clear the minimum-turns guard on POST .../end.
    for text in ["hi", "how are you", "nice weather"]:
        fake_client.queue_message_stream(["ok"])
        client.post(f"/practice/sessions/{session_id}/message", json={"text": text})

    malformed_payload = {
        "scores": {"warmth": 4.6, "curiosity": "3", "flow": 9},  # missing reciprocity, out-of-range flow
        "strengths": "Great warmth throughout.",  # bare string, not a list
        "focus_areas": ["Ask more follow-ups"],
        "drill_suggestion": None,
    }
    fake_client.queue_session_events(
        [agent_message_event(json.dumps(malformed_payload)), idle_event()]
    )

    end_resp = client.post(f"/practice/sessions/{session_id}/end")
    assert end_resp.status_code == 202

    # POST .../end kicks off grading as a BackgroundTask; TestClient runs
    # BackgroundTasks synchronously within the request, so it has already
    # completed by the time the GET below runs.
    report_resp = client.get(
        f"/practice/sessions/{session_id}/report", params={"user_id": "user-malformed"}
    )
    assert report_resp.status_code == 200
    report_body = report_resp.json()
    assert report_body["status"] == "ready"
    body = report_body["report"]
    assert body["scores"] == {"warmth": 5, "curiosity": 3, "flow": 5}
    assert "reciprocity" not in body["scores"]
    assert body["strengths"] == ["Great warmth throughout."]
    assert body["focus_areas"] == ["Ask more follow-ups"]
    assert body["drill_suggestion"] == ""
    assert body["parse_error"] is False
    # Response body must itself be a valid CoachReport.
    CoachReport(**body)


def test_end_route_with_unparseable_coordinator_output_degrades_cleanly(client, fake_client):
    """The coordinator emits nothing but chatter -- the route must still
    return 200 with the canonical parse_error shape, never a 500."""
    start_resp = client.post(
        "/practice/sessions", json={"user_id": "user-garbage", "scenario_id": "coffee-shop-line"}
    )
    session_id = start_resp.json()["session_id"]

    # 3 user turns to clear the minimum-turns guard on POST .../end.
    for text in ["hi", "how are you", "nice weather"]:
        fake_client.queue_message_stream(["ok"])
        client.post(f"/practice/sessions/{session_id}/message", json={"text": text})

    fake_client.queue_session_events(
        [agent_message_event("I couldn't produce structured JSON for this one, sorry!"), idle_event()]
    )

    end_resp = client.post(f"/practice/sessions/{session_id}/end")
    assert end_resp.status_code == 202

    report_resp = client.get(
        f"/practice/sessions/{session_id}/report", params={"user_id": "user-garbage"}
    )
    assert report_resp.status_code == 200
    report_body = report_resp.json()
    assert report_body["status"] == "ready"
    body = report_body["report"]
    assert body["parse_error"] is True
    assert body["scores"] == {}
    assert body["strengths"] == []
    assert body["focus_areas"] == []
    assert body["raw"] == "I couldn't produce structured JSON for this one, sorry!"
    CoachReport(**body)
