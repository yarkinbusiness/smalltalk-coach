"""T11: GET /users/{user_id}/progress/summary -- per-dimension score trend
data + summary stats behind the iOS progress screen's new chart header (see
ProgressListView.swift).

Kept as a pure function of db.get_progress's return shape, the same pattern
as recommend.py: `build_progress_summary(db.get_progress(user_id))` is all
main.py's route needs -- db.get_progress already returns exactly what's
needed (session_id, scenario_id, created_at, report) for every session with
a saved report, oldest-first, so no new db.py query was needed. Kept as its
own module (not folded into recommend.py, and not inlined in main.py)
because it answers a different question than recommend.py (a trend/summary
over *all* history vs. "what to practice next"), even though it shares
recommend.py's parse_error-filtering rule and weak-dimension signal (see
`valid_entries` / `current_focus_area` imports below) rather than
re-deriving either.
"""

from app.recommend import DIMENSIONS, current_focus_area, valid_entries


def build_progress_summary(progress: list[dict]) -> dict:
    """`progress` is db.get_progress(user_id)'s return shape: oldest-first
    list of {"session_id", "scenario_id", "created_at", "report"}.

    Returns:
        {
          "session_count": int,
          "current_focus_area": str | None,
          "dimensions": {
            "warmth":      [{"session_index": int, "score": int}, ...],
            "curiosity":   [...],
            "reciprocity": [...],
            "flow":        [...],
          },
        }

    Design decisions (the "gap" representation this task calls out):

    - parse_error sessions (`report["parse_error"] is True`, or a
      missing/malformed report -- the same `_is_valid` gate recommend.py
      uses, via `valid_entries`) are dropped *entirely*: not from
      `dimensions` only, but from `session_count` and from the index
      numbering too. They carry no real scores, so folding them in would
      force a choice between inventing a fake 0 (a fake dip in every
      dimension's trend line) or leaving a null placeholder at that slot
      (still a break in the line, and still implies "something was
      measured here"). Skipping them means the two real sessions on either
      side of a dropped one end up *adjacent* in the output -- e.g. a
      history of [real, parse_error, real] produces a 2-point series with
      session_index 0 and 1, never a 3-slot series with a hole at index 1.

    - `session_index` on each point is the session's zero-based position
      among *valid* sessions only, in chronological order (0, 1, 2, ...) --
      a parse_error session doesn't consume an index either. This is the
      x-axis value a client (the iOS Swift Charts line chart) plots
      against.

    - A dimension that a given *valid* session didn't score -- e.g.
      coach.normalize_report omitted a missing/garbage `warmth` key for
      that session, so `report["scores"]` simply lacks that key -- is
      represented by *omitting* that session_index from that dimension's
      list. No null, no 0, no placeholder of any kind. Concretely: one
      dimension's list can be shorter than `session_count`, and different
      dimensions' lists can name different sets of session_indexes. This
      is the same philosophy as the parse_error rule above, applied at
      finer (per-dimension, not per-session) grain -- a trend line for a
      dimension should only ever connect points that dimension actually
      scored, never dip through a fabricated value for a session it has no
      opinion on. A charting client draws each dimension's line only
      through the (session_index, score) points present for it, which
      naturally skips over gaps instead of interpolating through a fake
      value.

    - `session_count` counts only valid sessions -- the same population
      `dimensions` and `current_focus_area` are both computed over, so
      every number in this response describes the same set of sessions
      consistently (no "session_count includes parse_error rows but the
      chart doesn't" mismatch).

    - `current_focus_area` reuses recommend.py's own weak-dimension signal
      (see `recommend.current_focus_area`) -- the same
      RECENT_HISTORY_WINDOW-sized recent-history check that
      GET .../recommendation already acts on -- rather than re-deriving a
      second, potentially-divergent "weakest dimension" definition here.
      None if there's no repeated-enough weak signal yet (e.g. too little
      history, or no dimension clears recommend.py's REPEAT_THRESHOLD).

    Empty (or all-parse_error) `progress` returns the same shape with
    `session_count = 0`, `current_focus_area = None`, and every dimension
    mapped to `[]` -- never an error, and never missing keys a client would
    have to special-case around.
    """
    valid = valid_entries(progress)

    dimensions: dict[str, list[dict]] = {dim: [] for dim in DIMENSIONS}
    for index, entry in enumerate(valid):
        scores = entry["report"].get("scores") or {}
        for dim in DIMENSIONS:
            if dim in scores:
                dimensions[dim].append({"session_index": index, "score": scores[dim]})

    return {
        "session_count": len(valid),
        "current_focus_area": current_focus_area(valid),
        "dimensions": dimensions,
    }
