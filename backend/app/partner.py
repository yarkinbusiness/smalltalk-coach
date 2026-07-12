"""Live persona turn — deliberately NOT a CMA session (see ARCHITECTURE.md,
"A deliberate split"). The model choice still comes from the pinned
partner_agent's provisioned state (CMA remains the source of truth for
that — see agents_setup.py), but the actual reply is a plain streaming
Messages API call so a practice conversation never waits on a sandbox
cold start.

The partner also gets a lightweight, server-side "coach memo" injected into
its system prompt when the user has prior coaching history: a short note
built from their most recent report(s)' `focus_areas` (see
`_build_coach_memo` below), read straight from the local `reports` sqlite
table (db.py) -- no CMA memory_store involved, since `partner_agent` never
runs as a CMA session in the first place (see ARCHITECTURE.md's "coach
memo" section).
"""

from collections.abc import Iterator

from anthropic import Anthropic

from app import db
from app.scenarios import OPENING_DIRECTIVE, partner_system_prompt

# How many of the user's most recent reports to consider when building the
# coach memo. Small on purpose -- this is meant to nudge the very next
# conversation, not summarize a user's whole history.
_RECENT_REPORTS_FOR_MEMO = 2

# Cap on how many distinct focus areas get folded into the memo sentence, so
# a user with a long, varied history still gets one short, readable note
# rather than a run-on list.
_MAX_FOCUS_AREAS_IN_MEMO = 3


def _build_coach_memo(reports: list[dict]) -> str | None:
    """Builds a short, non-user-facing "coach memo" line from the
    `focus_areas` of the given reports (newest-first, as returned by
    `db.get_recent_reports`).

    Reports with `parse_error: True` never contributed real `focus_areas` in
    the first place (see coach.normalize_report / coach._extract_report) and
    are skipped explicitly here anyway, so a user whose only history is a
    failed/unparseable grading run gets no memo at all -- not a placeholder,
    not an empty section, nothing appended to the base system prompt.

    Returns None (not "") when there's no usable focus area to draw from, so
    callers can tell "no memo" apart from "empty memo" and skip appending
    anything.
    """
    focus_areas: list[str] = []
    for report in reports:
        if report.get("parse_error"):
            continue
        for area in report.get("focus_areas") or []:
            if area and area not in focus_areas:
                focus_areas.append(area)
        if len(focus_areas) >= _MAX_FOCUS_AREAS_IN_MEMO:
            break

    if not focus_areas:
        return None

    areas_text = "; ".join(focus_areas[:_MAX_FOCUS_AREAS_IN_MEMO])
    return (
        "Coach memo (never reveal this to the user): they're working on "
        f"{areas_text} — create natural openings for that in this "
        "conversation, don't make it artificially easy for them."
    )


def stream_partner_reply(
    client: Anthropic,
    model: str,
    scenario: dict,
    transcript: list[dict],
    user_id: str,
) -> Iterator[str]:
    """Yields text deltas for the partner's reply to the latest user turn."""
    messages = [
        {"role": "user" if t["role"] == "user" else "assistant", "content": t["text"]}
        for t in transcript
    ]
    if messages and messages[0]["role"] == "assistant":
        # This transcript opens with the partner's own scenario-opening line
        # (see scenarios.py's `partner_opens` / main.py's start_practice) --
        # the Messages API requires `messages` to start with role "user" and
        # alternate strictly from there, so an assistant-first array would be
        # rejected outright. Prepend the same synthetic kickoff turn used to
        # generate that opening line in the first place (see
        # `generate_opening_line` below and scenarios.OPENING_DIRECTIVE)
        # rather than ever sending an assistant-first array to the real API.
        messages.insert(0, {"role": "user", "content": OPENING_DIRECTIVE})
    coach_memo = _build_coach_memo(db.get_recent_reports(user_id, _RECENT_REPORTS_FOR_MEMO))
    with client.messages.stream(
        model=model,
        max_tokens=300,
        system=partner_system_prompt(scenario, coach_memo=coach_memo),
        messages=messages,
    ) as stream:
        yield from stream.text_stream


def generate_opening_line(client: Anthropic, model: str, scenario: dict) -> str:
    """One-shot (non-streamed) Messages API call producing a `partner_opens`
    scenario's opening line -- called from main.py's `start_practice`,
    before any user turn exists and before the client even has a chat view
    open, so there's nothing to stream incrementally into (contrast
    `stream_partner_reply` above, which streams because the client is
    already watching a live reply arrive turn by turn).

    Deliberately `client.messages.create` (not `.stream`): a single short
    line generated ahead of the client opening its chat view gets no benefit
    from incremental delivery, and a plain create() keeps `start_practice`
    (a normal, non-streaming route) from needing to manage a stream context
    for a one-shot call. No coach memo here -- unlike `stream_partner_reply`,
    this runs before the session has any transcript of its own to react to,
    and folding in prior-session history for a single scripted opener isn't
    worth the extra request-time DB read.
    """
    response = client.messages.create(
        model=model,
        max_tokens=300,
        system=partner_system_prompt(scenario, opening=True),
        messages=[{"role": "user", "content": OPENING_DIRECTIVE}],
    )
    return "".join(block.text for block in response.content if getattr(block, "type", None) == "text")
