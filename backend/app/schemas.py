from pydantic import BaseModel


class StartPracticeRequest(BaseModel):
    user_id: str
    scenario_id: str


class StartPracticeResponse(BaseModel):
    session_id: str
    scenario: dict
    # Populated only for a `partner_opens: True` scenario (see
    # scenarios.py/main.py's start_practice) -- the partner's opening line,
    # already persisted as the transcript's first (assistant) turn by the
    # time this response goes out. None for every other scenario, exactly
    # like before this field existed.
    opening_message: str | None = None


class SendMessageRequest(BaseModel):
    text: str


class CoachReport(BaseModel):
    # Constrained to `dict[str, int]` (not a bare `dict`) so this model is a
    # real second line of defense behind coach.normalize_report — a bare
    # `dict` would accept any value type and let a normalization bug (e.g. a
    # stray float/string score) slip through pydantic validation unnoticed.
    scores: dict[str, int]
    strengths: list[str] = []
    focus_areas: list[str] = []
    drill_suggestion: str = ""
    raw: str | None = None
    parse_error: bool = False


class EndPracticeResponse(BaseModel):
    """Body of the 202 returned by POST .../end once grading has been
    scheduled (not the report itself -- see ReportStatusResponse for that,
    via GET .../report)."""

    status: str = "grading"


class ReportStatusResponse(BaseModel):
    """Body of GET .../report. `status` is one of "grading" | "ready" |
    "failed" (or "active", if polled before .../end was ever called).
    `report` is only populated when `status == "ready"`. `error` is a short,
    client-safe hint populated only when `status == "failed"` -- never the
    raw exception text (see main.py's `_safe_error_message`)."""

    status: str
    report: CoachReport | None = None
    error: str | None = None


class RecommendationResponse(BaseModel):
    """Body of GET /users/{user_id}/recommendation -- see recommend.py's
    `recommend_next_scenario` for the full algorithm. `reason` is always a
    single, user-facing sentence explaining the pick."""

    scenario_id: str
    reason: str


class DimensionPoint(BaseModel):
    """One point in a per-dimension score series -- see
    ProgressSummaryResponse. `session_index` is this session's zero-based
    position among the user's chronological *valid* (non-parse_error)
    sessions -- not this point's position within its own dimension's list.
    Kept explicit (rather than relying on list position) specifically
    because a dimension's list can have gaps (see progress.py's
    `build_progress_summary` docstring): a dimension missing a handful of
    scores still needs its remaining points to land on the correct x-axis
    position when charted, instead of a gap silently compressing/shifting
    every point after it."""

    session_index: int
    score: int


class SessionDetailResponse(BaseModel):
    """Body of GET /practice/sessions/{session_id} -- T12: the full
    transcript + scenario + coaching report behind the iOS session-detail /
    replay screen (see SessionDetailView.swift). Lets the client re-read its
    own transcript next to the report that graded it -- previously the
    transcript that produced a report was stored in sqlite
    (practice_sessions.transcript_json) and never exposed to the client at
    all.

    Guarded by a required `user_id` query parameter that must match the
    session's actual owner (see main.py's `get_session_detail`) -- this app
    has no real auth, so a matching `user_id` is the same access-control
    convention every other user-scoped route here already relies on (e.g.
    GET /users/{user_id}/progress trusts whatever user_id is in its URL).
    See `get_session_detail`'s docstring for why a mismatched `user_id`
    returns 404 (not 403).

    `report` is None exactly when `db.get_report(session_id)` has nothing
    yet -- an `active` or `grading` session, or one whose grading run
    `failed`. This endpoint only reports the report's mere presence/absence;
    GET .../report already owns surfacing *why* there isn't one yet (status/
    polling/error detail), so this model deliberately doesn't duplicate
    that."""

    transcript: list[dict]
    scenario: dict
    report: CoachReport | None = None


class ProgressSummaryResponse(BaseModel):
    """Body of GET /users/{user_id}/progress/summary -- T11. See
    progress.py's `build_progress_summary` for the full derivation,
    especially why parse_error sessions are dropped entirely (never
    zero-scored) and why a session that didn't score a given dimension
    simply omits that session_index from that dimension's list (never a
    null/0 placeholder).

    `session_count` counts only valid (non-parse_error) sessions -- the
    same population `dimensions` and `current_focus_area` are both derived
    from, so every field in this response describes the same set of
    sessions. `current_focus_area` is None when there isn't a repeated-
    enough weak-dimension signal yet (see recommend.py's
    `current_focus_area` / `_find_weak_dimension`)."""

    session_count: int
    current_focus_area: str | None = None
    dimensions: dict[str, list[DimensionPoint]]
