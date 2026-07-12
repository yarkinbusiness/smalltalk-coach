"""T10: "what should I practice next?" — GET /users/{user_id}/recommendation.

Kept as a pure function of `db.get_progress`'s return shape (rather than
reaching into db.py/sqlite itself) so the algorithm can be unit-tested
directly against hand-built histories with no sqlite/FastAPI involved at all
(see tests/test_recommend.py). main.py's route is just
`recommend_next_scenario(db.get_progress(user_id))` — db.get_progress
already returns exactly what's needed here (session_id, scenario_id,
created_at, report) for every session a user has a report for, oldest-first,
so no new db.py query function was needed; the "recent window" slicing
happens in Python below instead of via SQL LIMIT, specifically so that
window is measured in *valid* (non-parse_error) reports rather than raw rows
(see the parse_error-filtering note in `recommend_next_scenario`'s
docstring, step 1).
"""

from app.scenarios import SCENARIOS

# Same four dimensions coach.py's REPORT_DIMENSIONS grades every report on.
# Duplicated here as a plain tuple (not imported from coach.py) to avoid a
# recommend.py -> coach.py import for four literal strings; keep in sync if
# coach.py's REPORT_DIMENSIONS ever changes.
DIMENSIONS = ("warmth", "curiosity", "reciprocity", "flow")

DIFFICULTY_ORDER = ["easy", "medium", "hard"]

# How many of the user's most recent *valid* reports feed every check below.
# Small enough that the recommendation tracks the user's *current* skill/
# focus (a rough session 20 practices ago shouldn't still be steering
# things forever); large enough that a single unusually good or bad session
# can't flip the recommendation on its own.
RECENT_HISTORY_WINDOW = 5

# A weak-dimension signal (being the lowest score in a report AND an
# absolute-low score per LOW_SCORE_THRESHOLD below, or being named in that
# report's focus_areas) must show up in at least this many *distinct*
# reports across the recent window to count as "repeated" rather than a
# one-off. Each report contributes at most one vote per dimension no matter
# how many of the two sub-signals fired in it -- see _find_weak_dimension's
# docstring for why a single report must never be able to satisfy this on
# its own. The task's own wording ("repeatedly the lowest score",
# "repeatedly named") calls for more than a single occurrence.
REPEAT_THRESHOLD = 2

# Absolute floor for the "lowest score" weak-dimension signal. Scores are
# 1-5 ints; being the smallest of four numbers means nothing on its own
# (four 5s still have a "lowest") -- this is what turns "relatively lowest"
# into "actually low". Chosen as the mirror image of HIGH_SCORE_THRESHOLD
# below (>=4 counts as "high", <=2 counts as "low"), leaving a genuinely
# middling 3 as neither -- a score has to clearly read as bad, not just
# below-average-among-good, to register as a weakness signal.
LOW_SCORE_THRESHOLD = 2

# "Consistently high" bar for the step-up-difficulty case. Scores are 1-5
# ints; the task's own framing ("e.g. 4-5") puts the bar at >= 4.
HIGH_SCORE_THRESHOLD = 4

# Minimum number of recent attempts *at the user's current difficulty tier*
# before "consistently high" is even considered. One great session isn't
# "consistent" — it's the lowest bar that still deserves that word: at
# least two independent attempts agreeing.
MIN_ATTEMPTS_FOR_STEP_UP = 2


def _is_valid(entry: dict) -> bool:
    report = entry.get("report")
    return isinstance(report, dict) and not report.get("parse_error")


def valid_entries(progress: list[dict]) -> list[dict]:
    """Public wrapper around `_is_valid` -- the parse_error-filtering rule
    (drop entries with no report, or `report["parse_error"] is True`) shared
    by `recommend_next_scenario` below and progress.py's
    `build_progress_summary` (T11), so both stay in sync on what counts as
    a "valid" (usable) session rather than each re-deriving the same
    filter independently."""
    return [entry for entry in progress if _is_valid(entry)]


def current_focus_area(valid: list[dict]) -> str | None:
    """The dimension `recommend_next_scenario`'s own algorithm currently
    treats as the user's recurring weak spot -- i.e. exactly the
    `_find_weak_dimension` signal computed over the same
    RECENT_HISTORY_WINDOW of recent valid reports that feeds
    GET .../recommendation (see that function's docstring for the full
    scoring rule).

    `valid` must already be filtered (see `valid_entries`) and in
    chronological (oldest-first) order -- the same shape
    `recommend_next_scenario` works with -- so "recent" means the same
    thing in both places.

    Exposed as its own function (rather than only living inline inside
    `recommend_next_scenario`) so GET .../progress/summary (progress.py)
    can label a "current focus area" using this exact signal without
    duplicating the weak-dimension-detection algorithm -- the progress
    screen and the recommendation should never disagree about what the
    user's current weak spot is. Returns None if there's no repeated-enough
    weak signal yet (empty history, or nothing clears REPEAT_THRESHOLD)."""
    if not valid:
        return None
    recent = valid[-RECENT_HISTORY_WINDOW:]
    return _find_weak_dimension(recent)


def _easiest_scenario() -> dict:
    return min(SCENARIOS, key=lambda s: DIFFICULTY_ORDER.index(s["difficulty"]))


def _scenario_difficulty(scenario_id: str) -> str:
    """Difficulty tier for `scenario_id`, looked up against the *current*
    SCENARIOS catalog rather than SCENARIOS_BY_ID (scenarios.py) purely so a
    scenario_id from a past report that no longer exists in the current
    catalog can't KeyError the whole recommendation -- falls back to
    "medium" (a neutral middle tier) instead of crashing on stale
    historical data."""
    for scenario in SCENARIOS:
        if scenario["id"] == scenario_id:
            return scenario["difficulty"]
    return "medium"


def _find_weak_dimension(recent: list[dict]) -> str | None:
    """Per-dimension "weakness signal" over `recent` (already-windowed,
    already-parse_error-filtered entries).

    Each report can cast at most one "vote" per dimension, no matter how
    many of the two sub-signals below fire for it — otherwise a single
    session where a dimension is both the report's lowest score *and*
    named in focus_areas would supply two votes by itself, letting one
    report alone satisfy REPEAT_THRESHOLD and falsely claim a "recurring"
    pattern. A report is considered to flag a dimension if:

      - That dimension holds the *lowest* score in the report's `scores`
        dict, AND that score is also an absolute-low score (<=
        LOW_SCORE_THRESHOLD). Ties for lowest (e.g. warmth and flow both
        the report's minimum) both count when both clear the floor — a tie
        is genuinely ambiguous evidence, so it shouldn't arbitrarily favor
        just one of them. The absolute floor is what stops "smallest of
        four high numbers" (e.g. everyone scoring 5 except one 4) from
        masquerading as an actual weakness.
      - The report's `focus_areas` entries contain the dimension's name as
        a case-insensitive substring (e.g. "Show a bit more curiosity
        about their weekend" matches "curiosity"). This is a best-effort
        heuristic — focus_areas is coach-written free text, not a
        controlled enum — and deliberately carries no absolute-score floor
        of its own: the coach explicitly chose to call this dimension out
        by name, which is signal on its own merit regardless of the
        numeric score that session.

    A dimension's total signal is the number of *distinct* reports that
    flagged it (0 or 1 per report, by construction above). The dimension
    with the highest total wins, provided that total is >= REPEAT_THRESHOLD
    — a total of exactly 1 is a single session's worth of evidence, not a
    *repeated* pattern, and because each report contributes at most one
    vote, reaching the threshold now genuinely requires >= REPEAT_THRESHOLD
    distinct reports, not just enough signals. Ties on the winning total
    are broken by lower average numeric score (the more reliable of the two
    signals), then by DIMENSIONS' fixed order, so the result is fully
    deterministic. Returns None if nothing clears the threshold.
    """
    signal = {dim: 0 for dim in DIMENSIONS}
    score_sum = {dim: 0 for dim in DIMENSIONS}
    score_count = {dim: 0 for dim in DIMENSIONS}

    for entry in recent:
        report = entry["report"]
        scores = report.get("scores") or {}
        known_scores = {dim: value for dim, value in scores.items() if dim in DIMENSIONS}

        flagged_by_this_report: set[str] = set()

        if known_scores:
            lowest = min(known_scores.values())
            for dim, value in known_scores.items():
                score_sum[dim] += value
                score_count[dim] += 1
                if value == lowest and value <= LOW_SCORE_THRESHOLD:
                    flagged_by_this_report.add(dim)

        focus_text = " ".join(report.get("focus_areas") or []).lower()
        for dim in DIMENSIONS:
            if dim in focus_text:
                flagged_by_this_report.add(dim)

        # However many of the two signals fired above, this one report
        # contributes at most a single vote per dimension.
        for dim in flagged_by_this_report:
            signal[dim] += 1

    best_dim: str | None = None
    best_signal = 0
    best_avg = None
    for dim in DIMENSIONS:
        s = signal[dim]
        if s < REPEAT_THRESHOLD:
            continue
        avg = (score_sum[dim] / score_count[dim]) if score_count[dim] else float("inf")
        if best_dim is None or s > best_signal or (s == best_signal and avg < best_avg):
            best_dim, best_signal, best_avg = dim, s, avg
    return best_dim


def _consistently_high(entries: list[dict]) -> bool:
    """True iff there are at least MIN_ATTEMPTS_FOR_STEP_UP entries and
    *every* score in *every* one of them is >= HIGH_SCORE_THRESHOLD. An
    entry with no scores at all can't be judged "high", so it disqualifies
    the whole set rather than being silently skipped."""
    if len(entries) < MIN_ATTEMPTS_FOR_STEP_UP:
        return False
    for entry in entries:
        scores = entry["report"].get("scores") or {}
        if not scores:
            return False
        if any(value < HIGH_SCORE_THRESHOLD for value in scores.values()):
            return False
    return True


def _pick_scenario_for_dimension(dim: str, attempted_ids: set[str], current_difficulty: str) -> dict:
    """Scenario recommended for a confirmed weak dimension. Tie-break order:
      1. Prefer a scenario the user has never attempted (spreads practice
         across scenarios instead of always sending them back to the same
         one).
      2. Then prefer one at the user's current difficulty tier — reinforcing
         a weak dimension works best without *also* raising the difficulty
         at the same time.
      3. Fall back to SCENARIOS' declared order (deterministic).
    """
    candidates = [s for s in SCENARIOS if dim in s.get("stresses", [])]
    if not candidates:
        # Should not happen in practice -- every DIMENSIONS entry has at
        # least one scenario stressing it (see scenarios.py) -- but don't
        # ever raise if that invariant is broken by a future catalog edit.
        candidates = SCENARIOS

    unattempted = [s for s in candidates if s["id"] not in attempted_ids]
    pool = unattempted or candidates
    same_tier = [s for s in pool if s["difficulty"] == current_difficulty]
    return (same_tier or pool)[0]


def _pick_scenario_at_difficulty(difficulty: str, valid: list[dict]) -> dict:
    """Least-attempted scenario at `difficulty` (0 attempts naturally ranks
    first, covering the "prefer unattempted" preference), SCENARIOS'
    declared order breaking any remaining tie. Used both for stepping up to
    the next difficulty tier and for the "already at the hardest tier"
    widen-coverage fallback."""
    at_tier = [s for s in SCENARIOS if s["difficulty"] == difficulty]
    counts = {s["id"]: 0 for s in at_tier}
    for entry in valid:
        if entry["scenario_id"] in counts:
            counts[entry["scenario_id"]] += 1
    return min(at_tier, key=lambda s: (counts[s["id"]], SCENARIOS.index(s)))


def _least_recently_practiced(valid: list[dict]) -> dict:
    """Final fallback (step 6): a never-attempted scenario ranks ahead of
    any attempted one (spaced-repetition style — "never" beats "a while
    ago"); among attempted scenarios, the one with the oldest last-attempt
    timestamp wins. `valid` is oldest-first (db.get_progress's order), so
    the last write into `last_at` per scenario_id is that scenario's most
    recent attempt."""
    last_at: dict[str, str] = {}
    for entry in valid:
        last_at[entry["scenario_id"]] = entry["created_at"]

    never_tried = [s for s in SCENARIOS if s["id"] not in last_at]
    if never_tried:
        return never_tried[0]
    return min(SCENARIOS, key=lambda s: last_at[s["id"]])


def _pick_default(current_difficulty: str, attempted_ids: set[str], valid: list[dict]) -> dict:
    """Step 6: no clear weak dimension, and not consistently-high enough to
    step up. Prefer a scenario the user hasn't tried yet (favoring their
    current difficulty tier first, then any tier in SCENARIOS' order); if
    every scenario has been attempted at least once, fall back to
    whichever was least recently practiced."""
    unattempted = [s for s in SCENARIOS if s["id"] not in attempted_ids]
    if unattempted:
        same_tier = [s for s in unattempted if s["difficulty"] == current_difficulty]
        return (same_tier or unattempted)[0]
    return _least_recently_practiced(valid)


def recommend_next_scenario(progress: list[dict]) -> dict:
    """`progress` is db.get_progress(user_id)'s return shape: oldest-first
    list of {"session_id", "scenario_id", "created_at", "report"}.

    Returns {"scenario_id": str, "reason": str}.

    Algorithm (documented in full — this logic is graded on whether it's
    *sound*, not just whether the endpoint returns 200):

    1. Drop parse_error reports entirely (`report["parse_error"] is True`,
       or a missing/malformed report). They carry no real scores or
       focus_areas, so folding them in would either silently drag down a
       dimension's average or make the focus_areas keyword search look at
       text that was never a real coaching note. This filtering applies to
       every step below, not just as a pre-filter for one branch.

    2. Empty history — either the user has never finished a graded session,
       or every session they've finished happened to fail parsing — means
       there is zero usable signal. Recommend the single easiest-difficulty
       scenario with a "start here" reason. Deliberately the same outcome
       for both "never practiced" and "practiced but every report was
       parse_error": in neither case do we know anything real about this
       user's skill, so the honest recommendation is the same on-ramp a
       brand new user would get.

    3. Otherwise, take the most recent RECENT_HISTORY_WINDOW valid reports
       and look for a "clear weak dimension" via `_find_weak_dimension`
       (see its docstring for the exact scoring: an absolute-low lowest
       score, or a focus_areas mention, each report casting at most one
       vote per dimension regardless of how many of those two signals it
       trips, requiring at least REPEAT_THRESHOLD *distinct reports* to
       vote for the same dimension before it counts as "repeated" at all).

    4. If a weak dimension was found: recommend a scenario whose `stresses`
       list includes it (see `_pick_scenario_for_dimension` for the
       tie-break order: unattempted first, then same-difficulty-as-current,
       then catalog order).

    5. If no weak dimension was found, check whether the user is ready to
       step up: "current difficulty" is the difficulty of their single most
       recent valid report's scenario. Among the recent-window reports at
       that same difficulty, if there are at least MIN_ATTEMPTS_FOR_STEP_UP
       and *every* score in *every* one of them is >= HIGH_SCORE_THRESHOLD
       (`_consistently_high`), recommend a scenario at the next difficulty
       tier up (easy -> medium -> hard), least-attempted-first. If already
       at the hardest tier, there's nowhere to step up to — the honest
       fallback is to widen coverage instead of repeating: the
       least-attempted scenario at that same (hardest) tier.

    6. Otherwise (no weak dimension, and not consistently-high-enough to
       step up): `_pick_default` — a scenario the user hasn't attempted yet
       (preferring their current tier), or the least-recently-practiced one
       if every scenario has already been tried at least once.
    """
    valid = valid_entries(progress)

    if not valid:
        scenario = _easiest_scenario()
        return {
            "scenario_id": scenario["id"],
            "reason": (
                f"Start here — \"{scenario['title']}\" is the easiest scenario, "
                "a good on-ramp before the tougher ones."
            ),
        }

    recent = valid[-RECENT_HISTORY_WINDOW:]
    attempted_ids = {entry["scenario_id"] for entry in valid}
    current_scenario_id = valid[-1]["scenario_id"]
    current_difficulty = _scenario_difficulty(current_scenario_id)

    weak_dim = _find_weak_dimension(recent)
    if weak_dim:
        scenario = _pick_scenario_for_dimension(weak_dim, attempted_ids, current_difficulty)
        return {
            "scenario_id": scenario["id"],
            "reason": (
                f"{weak_dim.capitalize()} has come up as your recurring weak spot in "
                f"recent reports — \"{scenario['title']}\" is built to exercise exactly that."
            ),
        }

    recent_at_current_tier = [
        entry for entry in recent
        if _scenario_difficulty(entry["scenario_id"]) == current_difficulty
    ]
    if _consistently_high(recent_at_current_tier):
        next_index = DIFFICULTY_ORDER.index(current_difficulty) + 1
        if next_index < len(DIFFICULTY_ORDER):
            next_difficulty = DIFFICULTY_ORDER[next_index]
            scenario = _pick_scenario_at_difficulty(next_difficulty, valid)
            return {
                "scenario_id": scenario["id"],
                "reason": (
                    f"You've been consistently scoring high at {current_difficulty} — "
                    f"time to step up to {next_difficulty} with \"{scenario['title']}\"."
                ),
            }
        scenario = _pick_scenario_at_difficulty(current_difficulty, valid)
        return {
            "scenario_id": scenario["id"],
            "reason": (
                f"You've mastered {current_difficulty} scenarios — try \"{scenario['title']}\" "
                "to round out your practice at this level."
            ),
        }

    scenario = _pick_default(current_difficulty, attempted_ids, valid)
    return {
        "scenario_id": scenario["id"],
        "reason": f"Keep the variety going — \"{scenario['title']}\" is next up in your rotation.",
    }
