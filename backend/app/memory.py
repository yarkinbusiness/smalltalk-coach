"""CMA memory_store wiring — the "Remember user preferences" pattern.

One memory_store per user, attached as a session resource so
coach_coordinator can read a user's history while synthesizing a report.
Our own progress screen does NOT read this store back — it reads the
`reports` table in db.py, which we already populated ourselves. This store
exists purely to give the *coordinator agent* cross-session context.
"""

from anthropic import Anthropic

from app import db


def ensure_user_memory_store(client: Anthropic, user_id: str) -> str:
    existing = db.get_user_memory_store(user_id)
    if existing:
        return existing
    store = client.beta.memory_stores.create(
        name=f"smalltalk-coach-user-{user_id}",
        description="Small-talk practice history and recurring focus areas for one user.",
    )
    db.set_user_memory_store(user_id, store.id)
    return store.id


def record_session_summary(
    client: Anthropic, memory_store_id: str, session_id: str, report: dict
) -> None:
    content = (
        f"Session {session_id}\n"
        f"Scores: {report.get('scores')}\n"
        f"Focus areas: {report.get('focus_areas')}\n"
        f"Drill suggested: {report.get('drill_suggestion')}\n"
    )
    client.beta.memory_stores.memories.create(
        memory_store_id=memory_store_id,
        path=f"/sessions/{session_id}.md",
        content=content,
    )


# T14: onboarding's third screen ("what do you struggle with most?") offers
# exactly these four picks, or "Skip" -- a closed set (like scenario_id is a
# closed set of known scenarios in scenarios.py), not free text, so there's
# never an ambiguous/unbounded string to store or to have coach_coordinator
# make sense of. Keys are the wire values the iOS client sends/main.py
# validates against; values are the human-readable description folded into
# the memory-store content below.
STRUGGLE_OPTIONS: dict[str, str] = {
    "freezing_on_openers": (
        "Freezes up on how to start a conversation -- doesn't know what to "
        "say first."
    ),
    "only_asking_questions": (
        "Falls back on asking question after question and runs out of "
        "things to add of their own."
    ),
    "only_talking_about_yourself": (
        "Tends to dominate with their own stories/opinions instead of "
        "drawing the other person out."
    ),
    "awkward_exits": (
        "Doesn't know how to end a conversation gracefully -- exits feel "
        "abrupt or drag on too long."
    ),
}


def record_struggle_pick(
    client: Anthropic, memory_store_id: str, user_id: str, struggle: str
) -> None:
    """Seeds the user's stated onboarding struggle-pick (OnboardingView's
    third screen, "what do you struggle with most?") into their memory
    store -- the exact same `client.beta.memory_stores.memories.create(...)`
    mechanism `record_session_summary` above already uses to write a
    session's coaching summary, just a different `path`/`content`. Written
    once, at onboarding time -- typically before the user's first real
    coaching report exists -- so that very first report can read this back
    the same way it reads every later session's summary: as one more file
    under this user's memory_store, available to coach_coordinator to draw
    on if useful (this deliberately does not change coach.py's coordinator
    prompt to explicitly consume it -- that's a stretch goal, not required
    for this to be durably recorded).

    `struggle` must be one of `STRUGGLE_OPTIONS`'s keys -- main.py's
    `onboard_user` validates that before calling this, so this function
    itself does a plain dict lookup rather than re-validating.

    Only ever called for a *stated* pick -- see main.py's `onboard_user`,
    which never calls this for the "Skip" case -- so a user who skips
    onboarding's struggle question never gets an entry written here at all,
    bogus or otherwise.
    """
    description = STRUGGLE_OPTIONS[struggle]
    content = (
        f"Onboarding: user {user_id} said their biggest small-talk struggle is:\n"
        f"{struggle} -- {description}\n"
    )
    client.beta.memory_stores.memories.create(
        memory_store_id=memory_store_id,
        path="/onboarding/struggle_pick.md",
        content=content,
    )
