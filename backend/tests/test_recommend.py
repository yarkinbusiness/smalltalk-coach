"""T10: recommend.recommend_next_scenario -- the "what should I practice
next?" algorithm behind GET /users/{user_id}/recommendation.

Exercised here as a pure function against hand-built synthetic histories
(recommend_next_scenario's only input is db.get_progress's return shape --
see recommend.py's module docstring for why no sqlite/FastAPI is needed to
test the logic itself). test_recommend_endpoint.py separately proves the
route actually wires this function up to real db-backed data.

Each test is designed so the *correct* recommendation is unambiguous given
the synthetic input -- not just "some scenario_id came back" -- per the
task's grading bar.
"""

from app.recommend import recommend_next_scenario
from app.scenarios import SCENARIOS_BY_ID


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


def test_empty_history_recommends_easiest_scenario_with_start_here_reason():
    result = recommend_next_scenario([])

    # coffee-shop-line is the only "easy" scenario in the catalog -- the
    # easiest possible on-ramp for a user with zero history.
    assert result["scenario_id"] == "coffee-shop-line"
    assert SCENARIOS_BY_ID[result["scenario_id"]]["difficulty"] == "easy"
    assert "start here" in result["reason"].lower()


def test_history_of_only_parse_errors_is_treated_as_empty():
    """A user who has attempted sessions, but every single one failed to
    parse into a real report, has exactly as much *usable* signal as a
    brand new user -- zero. Should get the identical recommendation."""
    progress = [
        _entry("networking-mixer", _report({}, parse_error=True), created_at="2026-01-01T00:00:00+00:00"),
        _entry("elevator-coworker", _report({}, parse_error=True), created_at="2026-01-02T00:00:00+00:00"),
    ]
    result = recommend_next_scenario(progress)

    assert result["scenario_id"] == "coffee-shop-line"
    assert "start here" in result["reason"].lower()


# --- recurring weak dimension --------------------------------------------


def test_recurring_low_score_recommends_scenario_stressing_that_dimension():
    """reciprocity is unambiguously the lowest score in every recent
    report -- dinner-party-stranger is the only scenario whose `stresses`
    includes reciprocity, so it must be the pick."""
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
    result = recommend_next_scenario(progress)

    assert result["scenario_id"] == "dinner-party-stranger"
    assert "reciprocity" in result["reason"].lower()
    assert "dinner-party-stranger" not in {
        e["scenario_id"] for e in progress
    }  # confirms this is a genuinely *new* recommendation, not a repeat


def test_focus_area_mentions_alone_can_surface_the_weak_dimension():
    """Every score ties at 3 (so the numeric "lowest score" signal is
    evenly split across all four dimensions -- +1 each, per report,
    self-cancelling), but "curiosity" is explicitly named in focus_areas
    both times. That extra, dimension-specific signal should be enough to
    single curiosity out as the recommendation target."""
    tied_scores = {"warmth": 3, "curiosity": 3, "reciprocity": 3, "flow": 3}
    progress = [
        _entry(
            "elevator-coworker",
            _report(tied_scores, focus_areas=["Show a bit more curiosity about their weekend."]),
            created_at="2026-01-01T00:00:00+00:00",
        ),
        _entry(
            "elevator-coworker",
            _report(tied_scores, focus_areas=["Bring more curiosity into your follow-up questions."]),
            created_at="2026-01-02T00:00:00+00:00",
        ),
    ]
    result = recommend_next_scenario(progress)

    assert result["scenario_id"] == "networking-mixer"  # the scenario that stresses curiosity
    assert "curiosity" in result["reason"].lower()


def test_single_low_score_does_not_count_as_a_repeated_weak_dimension():
    """One bad report where reciprocity dips is not a *pattern* -- with
    only one recent report total, nothing clears REPEAT_THRESHOLD, so this
    must NOT trigger the weak-dimension branch (and, since a single report
    also can't satisfy MIN_ATTEMPTS_FOR_STEP_UP, must fall through to the
    default rotation branch instead)."""
    progress = [
        _entry(
            "networking-mixer",
            _report({"warmth": 4, "curiosity": 4, "reciprocity": 2, "flow": 4}),
            created_at="2026-01-01T00:00:00+00:00",
        ),
    ]
    result = recommend_next_scenario(progress)

    # Not the reciprocity-stressing scenario -- one low score isn't enough
    # evidence yet.
    assert result["scenario_id"] != "dinner-party-stranger"


def test_single_report_flagged_two_ways_does_not_count_as_repeated():
    """Regression for the "repeated == 2 signals, not 2 reports" bug: a
    single report where reciprocity is *both* the report's lowest score
    (and an absolute-low 1, so it would legitimately clear the floor) *and*
    named in focus_areas is exactly one report's worth of evidence. It must
    NOT reach REPEAT_THRESHOLD on its own -- that takes >= 2 *distinct*
    reports voting for the same dimension, not >= 2 signals from one."""
    progress = [
        _entry(
            "networking-mixer",
            _report(
                {"warmth": 4, "curiosity": 4, "reciprocity": 1, "flow": 4},
                focus_areas=["Work on reciprocity -- share a bit about yourself too."],
            ),
            created_at="2026-01-01T00:00:00+00:00",
        ),
    ]
    result = recommend_next_scenario(progress)

    # Not the reciprocity-stressing scenario -- one report, however loudly
    # it flags reciprocity, is still just one report.
    assert result["scenario_id"] != "dinner-party-stranger"
    assert "recurring" not in result["reason"].lower()


def test_flat_all_high_scores_do_not_produce_a_false_weak_dimension():
    """Regression for the "relative lowest with no absolute floor" bug:
    two reports where *every* score is a flat 5 have a "lowest" in the
    mathematical sense (every dimension ties for it) but nothing is
    remotely a weakness. Must NOT trigger the weak-dimension branch --
    must fall through to the consistently-high step-up check instead."""
    progress = [
        _entry(
            "coffee-shop-line",
            _report({"warmth": 5, "curiosity": 5, "reciprocity": 5, "flow": 5}),
            created_at="2026-01-01T00:00:00+00:00",
        ),
        _entry(
            "coffee-shop-line",
            _report({"warmth": 5, "curiosity": 5, "reciprocity": 5, "flow": 5}),
            created_at="2026-01-02T00:00:00+00:00",
        ),
    ]
    result = recommend_next_scenario(progress)

    # No scenario stresses a phantom "weak spot" pulled out of flat 5s --
    # and the reason text must never call a 5 a weak spot.
    assert "weak spot" not in result["reason"].lower()
    assert "warmth" not in result["reason"].lower()


# --- consistently high scores -> step up difficulty ----------------------


def test_consistently_high_scores_at_current_tier_recommends_stepping_up():
    """Two recent attempts at "medium" difficulty, every score >= 4, and
    the *lowest* score varies between reports (so no single dimension
    racks up a repeated weak-dimension signal). This is the textbook
    "doing great, time to level up" case -- expect a "hard" scenario back,
    not a repeat of the medium ones just aced."""
    progress = [
        _entry(
            "elevator-coworker",
            _report({"warmth": 5, "curiosity": 4, "reciprocity": 5, "flow": 5}),
            created_at="2026-01-01T00:00:00+00:00",
        ),
        _entry(
            "networking-mixer",
            _report({"warmth": 4, "curiosity": 5, "reciprocity": 5, "flow": 5}),
            created_at="2026-01-02T00:00:00+00:00",
        ),
    ]
    result = recommend_next_scenario(progress)

    recommended = SCENARIOS_BY_ID[result["scenario_id"]]
    assert recommended["difficulty"] == "hard"
    assert result["scenario_id"] in {"dinner-party-stranger", "gym-regular"}
    assert "step up" in result["reason"].lower() or "hard" in result["reason"].lower()


def test_flat_high_scores_at_easy_tier_steps_up_to_medium():
    """Regression for the reviewer-found bug: two flat all-5 reports at the
    easy tier used to falsely trigger the weak-dimension branch (every
    dimension ties for "lowest" twice, tie-break arbitrarily picks warmth)
    and recommend a *hard* scenario with a factually-false "recurring weak
    spot" reason, skipping medium entirely. With the absolute floor on the
    lowest-score signal, flat 5s can never look like a weakness, so this
    must fall through to the step-up check and recommend a *medium*
    scenario -- one tier up from easy, not two, and not a demotion."""
    progress = [
        _entry(
            "coffee-shop-line",
            _report({"warmth": 5, "curiosity": 5, "reciprocity": 5, "flow": 5}),
            created_at="2026-01-01T00:00:00+00:00",
        ),
        _entry(
            "coffee-shop-line",
            _report({"warmth": 5, "curiosity": 5, "reciprocity": 5, "flow": 5}),
            created_at="2026-01-02T00:00:00+00:00",
        ),
    ]
    result = recommend_next_scenario(progress)

    recommended = SCENARIOS_BY_ID[result["scenario_id"]]
    assert recommended["difficulty"] == "medium"
    assert "step up" in result["reason"].lower()
    assert "weak spot" not in result["reason"].lower()


def test_stable_relative_lowest_but_still_high_scores_steps_up_to_hard():
    """Regression for the reviewer-found bug: two reports at medium, every
    score >= 4, with warmth stably the *relative* lowest both times (a
    completely ordinary shape for a genuinely strong user -- most people
    have *some* dimension that's their relative weakest, even when every
    score is good) used to falsely fire the weak-dimension branch and
    demote the user to an *easy* scenario. With the absolute floor (a 4 is
    not an absolute-low score), this must NOT be treated as a weakness and
    must instead recognize "consistently high" and step up to *hard*."""
    progress = [
        _entry(
            "elevator-coworker",
            _report({"warmth": 4, "curiosity": 5, "reciprocity": 5, "flow": 5}),
            created_at="2026-01-01T00:00:00+00:00",
        ),
        _entry(
            "networking-mixer",
            _report({"warmth": 4, "curiosity": 4, "reciprocity": 5, "flow": 5}),
            created_at="2026-01-02T00:00:00+00:00",
        ),
    ]
    result = recommend_next_scenario(progress)

    recommended = SCENARIOS_BY_ID[result["scenario_id"]]
    assert recommended["difficulty"] == "hard"
    assert "step up" in result["reason"].lower()
    assert "weak spot" not in result["reason"].lower()


def test_high_scores_but_too_few_attempts_does_not_step_up():
    """A single high-scoring session at medium difficulty is not
    "consistent" (MIN_ATTEMPTS_FOR_STEP_UP == 2) -- must NOT recommend a
    hard scenario off the back of just one good result."""
    progress = [
        _entry(
            "elevator-coworker",
            _report({"warmth": 5, "curiosity": 5, "reciprocity": 5, "flow": 5}),
            created_at="2026-01-01T00:00:00+00:00",
        ),
    ]
    result = recommend_next_scenario(progress)

    recommended = SCENARIOS_BY_ID[result["scenario_id"]]
    assert recommended["difficulty"] != "hard"


def test_consistently_high_at_hardest_tier_widens_coverage_instead_of_stepping_up():
    """There is no tier past "hard" -- two aced attempts at the *same* hard
    scenario should recommend the other, not-yet-tried hard scenario
    (widening coverage) rather than erroring or looping back to a lower
    tier."""
    progress = [
        _entry(
            "dinner-party-stranger",
            _report({"warmth": 5, "curiosity": 4, "reciprocity": 5, "flow": 5}),
            created_at="2026-01-01T00:00:00+00:00",
        ),
        _entry(
            "dinner-party-stranger",
            _report({"warmth": 4, "curiosity": 5, "reciprocity": 5, "flow": 5}),
            created_at="2026-01-02T00:00:00+00:00",
        ),
    ]
    result = recommend_next_scenario(progress)

    assert result["scenario_id"] == "gym-regular"  # the untried hard scenario
    assert SCENARIOS_BY_ID[result["scenario_id"]]["difficulty"] == "hard"


# --- parse_error reports must not corrupt the computation -----------------


def test_parse_error_reports_are_excluded_from_weak_dimension_computation():
    """Two genuinely valid reports unambiguously point at reciprocity as
    the weak dimension. Interspersed are three parse_error reports
    deliberately stuffed with scores/focus_areas that would swing the
    result toward "warmth" if they were (wrongly) counted. If the
    parse_error filter works, warmth's corrupting signal must be ignored
    and reciprocity must still win."""
    corrupting_parse_error_reports = [
        _entry(
            "coffee-shop-line",
            _report(
                {"warmth": 1, "curiosity": 5, "reciprocity": 5, "flow": 5},
                focus_areas=["Warmth needs work."],
                parse_error=True,
            ),
            created_at=f"2026-01-0{i}T00:00:00+00:00",
        )
        for i in (4, 5, 6)
    ]
    valid_reports = [
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
    ]
    progress = valid_reports + corrupting_parse_error_reports

    result = recommend_next_scenario(progress)

    assert result["scenario_id"] == "dinner-party-stranger"  # stresses reciprocity, not warmth
    assert "reciprocity" in result["reason"].lower()


def test_parse_error_reports_do_not_count_as_attempts():
    """A scenario the user "tried" but which parse_error'd should still be
    eligible to be *recommended back* -- it doesn't count as a real,
    graded attempt. Here dinner-party-stranger's only "attempt" is a
    parse_error, and reciprocity is the recurring weak dimension from the
    genuinely valid reports, so dinner-party-stranger (unattempted, for
    recommendation purposes) must still be the pick."""
    progress = [
        _entry(
            "dinner-party-stranger",
            _report({}, parse_error=True),
            created_at="2026-01-01T00:00:00+00:00",
        ),
        _entry(
            "networking-mixer",
            _report({"warmth": 4, "curiosity": 4, "reciprocity": 2, "flow": 4}),
            created_at="2026-01-02T00:00:00+00:00",
        ),
        _entry(
            "elevator-coworker",
            _report({"warmth": 3, "curiosity": 4, "reciprocity": 1, "flow": 4}),
            created_at="2026-01-03T00:00:00+00:00",
        ),
    ]
    result = recommend_next_scenario(progress)

    assert result["scenario_id"] == "dinner-party-stranger"
