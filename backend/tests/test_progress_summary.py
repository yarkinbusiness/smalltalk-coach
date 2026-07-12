"""T11: progress.build_progress_summary -- the per-dimension score trend +
summary stats behind GET /users/{user_id}/progress/summary.

Exercised here as a pure function against hand-built synthetic histories
(build_progress_summary's only input is db.get_progress's return shape --
see progress.py's module docstring). test_progress_summary_endpoint.py
separately proves the route actually wires this function up to real
db-backed data.
"""

from app.progress import build_progress_summary

DIMENSIONS = ("warmth", "curiosity", "reciprocity", "flow")


def _report(scores, focus_areas=None, *, parse_error=False):
    """A well-formed (or, if parse_error=True, deliberately malformed)
    CoachReport-shaped dict, matching what coach.normalize_report actually
    produces."""
    return {
        "scores": scores,
        "strengths": [],
        "focus_areas": focus_areas or [],
        "drill_suggestion": "",
        "raw": None,
        "parse_error": parse_error,
    }


def _entry(scenario_id, report, created_at="2026-01-01T00:00:00+00:00", session_id=None):
    return {
        "session_id": session_id or f"session-{scenario_id}-{created_at}",
        "scenario_id": scenario_id,
        "created_at": created_at,
        "report": report,
    }


# --- empty history -----------------------------------------------------


def test_empty_history_returns_zero_shape_not_an_error():
    result = build_progress_summary([])

    assert result["session_count"] == 0
    assert result["current_focus_area"] is None
    assert result["dimensions"] == {dim: [] for dim in DIMENSIONS}


def test_history_of_only_parse_errors_returns_the_same_zero_shape():
    """A user who has attempted sessions, but every single one failed to
    parse, has exactly as much usable signal as a brand new user -- zero.
    session_count must reflect that (0), not the number of raw attempts."""
    progress = [
        _entry("networking-mixer", _report({}, parse_error=True), created_at="2026-01-01T00:00:00+00:00"),
        _entry("elevator-coworker", _report({}, parse_error=True), created_at="2026-01-02T00:00:00+00:00"),
    ]
    result = build_progress_summary(progress)

    assert result["session_count"] == 0
    assert result["current_focus_area"] is None
    assert result["dimensions"] == {dim: [] for dim in DIMENSIONS}


# --- chronological ordering ----------------------------------------------


def test_series_is_in_correct_chronological_order():
    """Three real sessions, each dimension strictly increasing over time --
    the output series for every dimension must read in the same
    chronological order as the input (oldest-first), with session_index
    0, 1, 2 matching that order, not sorted by score or reversed."""
    progress = [
        _entry(
            "networking-mixer",
            _report({"warmth": 2, "curiosity": 2, "reciprocity": 2, "flow": 2}),
            created_at="2026-01-01T00:00:00+00:00",
        ),
        _entry(
            "elevator-coworker",
            _report({"warmth": 3, "curiosity": 3, "reciprocity": 3, "flow": 3}),
            created_at="2026-01-02T00:00:00+00:00",
        ),
        _entry(
            "coffee-shop-line",
            _report({"warmth": 4, "curiosity": 4, "reciprocity": 4, "flow": 4}),
            created_at="2026-01-03T00:00:00+00:00",
        ),
    ]
    result = build_progress_summary(progress)

    assert result["session_count"] == 3
    for dim in DIMENSIONS:
        series = result["dimensions"][dim]
        assert [point["session_index"] for point in series] == [0, 1, 2]
        assert [point["score"] for point in series] == [2, 3, 4]


# --- parse_error exclusion (the critical case) ----------------------------


def test_parse_error_between_two_real_sessions_is_skipped_not_zero_scored():
    """A parse_error session sits between two real, scored sessions. The
    resulting series must have exactly 2 points (not 3 with a fake 0/None
    in the middle), and those 2 real points must be *adjacent* in the
    output -- session_index 0 and 1, not 0 and 2 with a gap at 1."""
    progress = [
        _entry(
            "networking-mixer",
            _report({"warmth": 5, "curiosity": 5, "reciprocity": 5, "flow": 5}),
            created_at="2026-01-01T00:00:00+00:00",
        ),
        _entry(
            "elevator-coworker",
            _report({}, parse_error=True),
            created_at="2026-01-02T00:00:00+00:00",
        ),
        _entry(
            "coffee-shop-line",
            _report({"warmth": 1, "curiosity": 1, "reciprocity": 1, "flow": 1}),
            created_at="2026-01-03T00:00:00+00:00",
        ),
    ]
    result = build_progress_summary(progress)

    # session_count is the *real* (non-parse_error) count: 2, not 3.
    assert result["session_count"] == 2

    for dim in DIMENSIONS:
        series = result["dimensions"][dim]
        assert len(series) == 2  # not 3 -- the parse_error session contributes no point
        assert [point["session_index"] for point in series] == [0, 1]  # adjacent, no gap at 1
        assert [point["score"] for point in series] == [5, 1]  # the two real sessions, in order


def test_parse_error_first_or_last_is_also_skipped():
    """Sanity check that exclusion isn't special-cased to only the
    "sandwiched" position -- a parse_error at either end of the history is
    dropped the same way."""
    progress = [
        _entry("networking-mixer", _report({}, parse_error=True), created_at="2026-01-01T00:00:00+00:00"),
        _entry(
            "elevator-coworker",
            _report({"warmth": 4, "curiosity": 4, "reciprocity": 4, "flow": 4}),
            created_at="2026-01-02T00:00:00+00:00",
        ),
        _entry("coffee-shop-line", _report({}, parse_error=True), created_at="2026-01-03T00:00:00+00:00"),
    ]
    result = build_progress_summary(progress)

    assert result["session_count"] == 1
    for dim in DIMENSIONS:
        assert result["dimensions"][dim] == [{"session_index": 0, "score": 4}]


# --- per-dimension gaps (a valid session that didn't score every dimension) --


def test_missing_dimension_in_one_session_is_omitted_not_null_or_zero():
    """A real (non-parse_error) session whose report is missing a `warmth`
    key entirely (e.g. coach.normalize_report dropped a garbage/missing
    value for it) must not appear at all in warmth's series -- no null, no
    0 -- while the other three dimensions (which this session did score)
    still include it at the correct session_index, and the *next* real
    session's warmth point still lands at session_index 1, not 2."""
    progress = [
        _entry(
            "networking-mixer",
            _report({"curiosity": 3, "reciprocity": 3, "flow": 3}),  # warmth missing
            created_at="2026-01-01T00:00:00+00:00",
        ),
        _entry(
            "elevator-coworker",
            _report({"warmth": 5, "curiosity": 5, "reciprocity": 5, "flow": 5}),
            created_at="2026-01-02T00:00:00+00:00",
        ),
    ]
    result = build_progress_summary(progress)

    assert result["session_count"] == 2
    assert result["dimensions"]["warmth"] == [{"session_index": 1, "score": 5}]
    for dim in ("curiosity", "reciprocity", "flow"):
        assert [p["session_index"] for p in result["dimensions"][dim]] == [0, 1]


# --- session count -----------------------------------------------------


def test_session_count_matches_real_non_parse_error_count():
    progress = [
        _entry(
            "networking-mixer",
            _report({"warmth": 3, "curiosity": 3, "reciprocity": 3, "flow": 3}),
            created_at="2026-01-01T00:00:00+00:00",
        ),
        _entry("elevator-coworker", _report({}, parse_error=True), created_at="2026-01-02T00:00:00+00:00"),
        _entry(
            "coffee-shop-line",
            _report({"warmth": 4, "curiosity": 4, "reciprocity": 4, "flow": 4}),
            created_at="2026-01-03T00:00:00+00:00",
        ),
        _entry(
            "dinner-party-stranger",
            _report({"warmth": 5, "curiosity": 5, "reciprocity": 5, "flow": 5}),
            created_at="2026-01-04T00:00:00+00:00",
        ),
    ]
    result = build_progress_summary(progress)

    assert result["session_count"] == 3  # 4 attempts, 1 parse_error -> 3 real


# --- current_focus_area shares recommend.py's signal ----------------------


def test_current_focus_area_matches_recommend_pys_weak_dimension_signal():
    """Same synthetic history as
    test_recommend.test_recurring_low_score_recommends_scenario_stressing_that_dimension
    -- reciprocity is unambiguously the recurring weak spot. build_progress_summary's
    current_focus_area must name the same dimension recommend_next_scenario
    would act on, since both are meant to read the same underlying signal."""
    progress = [
        _entry(
            "networking-mixer",
            _report({"warmth": 4, "curiosity": 4, "reciprocity": 2, "flow": 4}),
            created_at="2026-01-01T00:00:00+00:00",
        ),
        _entry(
            "elevator-coworker",
            _report({"warmth": 3, "curiosity": 4, "reciprocity": 1, "flow": 4}),
            created_at="2026-01-02T00:00:00+00:00",
        ),
        _entry(
            "networking-mixer",
            _report({"warmth": 4, "curiosity": 3, "reciprocity": 2, "flow": 3}),
            created_at="2026-01-03T00:00:00+00:00",
        ),
    ]
    result = build_progress_summary(progress)

    assert result["current_focus_area"] == "reciprocity"


def test_current_focus_area_is_none_without_a_repeated_signal():
    """A single low-scoring report is not a *pattern* (mirrors
    test_recommend.test_single_low_score_does_not_count_as_a_repeated_weak_dimension)
    -- current_focus_area must be None, not a guess based on one data point."""
    progress = [
        _entry(
            "networking-mixer",
            _report({"warmth": 4, "curiosity": 4, "reciprocity": 2, "flow": 4}),
            created_at="2026-01-01T00:00:00+00:00",
        ),
    ]
    result = build_progress_summary(progress)

    assert result["current_focus_area"] is None
