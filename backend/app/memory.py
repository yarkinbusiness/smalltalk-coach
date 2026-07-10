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
