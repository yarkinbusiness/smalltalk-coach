"""Local persistence for what the app owns directly: which memory_store_id
belongs to which user, the live transcript of each in-progress practice
conversation, and past coaching reports (for the iOS progress screen).

This is SQLite, not a CMA resource — the CMA memory_store exists so the
*coach_coordinator agent* can read a user's history server-side while
synthesizing a report; this DB is so *our own backend* can render a chat
view and a progress view without re-querying CMA for things we already
produced ourselves. Fine for one backend process; move to Postgres before
running multiple backend instances against the same DB file.
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from app.config import DB_PATH

# --- Session status model (T6) ---------------------------------------------
#
# `status` has grown from a two-value active/ended flag into a small state
# machine for the async grading flow (see main.py's POST .../end):
#
#   active   -- session in progress, transcript still being appended to.
#   grading  -- POST .../end accepted the transcript and kicked off the real
#               CMA coach_coordinator run as a FastAPI BackgroundTask; the
#               HTTP response has already been sent (202) and the coordinator
#               may still be running for anywhere from seconds to tens of
#               seconds.
#   ended    -- the background run completed successfully; `reports` has a
#               row for this session_id and GET .../report returns it.
#   failed   -- the background run raised; `report_error` holds a short,
#               client-safe hint (never the raw exception text). A fresh
#               POST .../end is allowed to retry from this state (unlike
#               `grading`/`ended`, which reject a second POST with 409).
#
# Transitions: active -> grading -> (ended | failed); failed -> grading (retry).
# `report_error` is cleared on every transition *into* grading or ended, so a
# stale error from a previous failed attempt never lingers once a retry (or
# an eventual success) supersedes it.
#
# Reused the existing `status` column rather than introducing a parallel
# "report_status" column -- there is exactly one thing being tracked (what
# state this session's grading is in), so a second column would just be two
# names for one fact. `get_practice_session` / `mark_session_ended` keep
# their existing names and behavior for callers that already use them.
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    memory_store_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS practice_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    transcript_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'active',
    report_error TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reports (
    session_id TEXT PRIMARY KEY,
    report_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


@contextmanager
def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _migrate(conn: sqlite3.Connection) -> None:
    """Additive, idempotent migration for columns added after the original
    SCHEMA shipped. `CREATE TABLE IF NOT EXISTS` (above) only creates the
    table when it's missing entirely -- it does nothing to an existing
    on-disk DB file from before `report_error` existed, so that column is
    retrofitted here via ALTER TABLE, guarded by a PRAGMA table_info check
    so re-running it is a no-op."""
    existing_cols = {row["name"] for row in conn.execute("PRAGMA table_info(practice_sessions)")}
    if "report_error" not in existing_cols:
        conn.execute("ALTER TABLE practice_sessions ADD COLUMN report_error TEXT")


def init_db() -> None:
    with _conn() as conn:
        conn.executescript(SCHEMA)
        _migrate(conn)


def recover_stale_grading_sessions(message: str) -> int:
    """Startup-time sweep: any session still in `grading` status when this
    process boots cannot possibly have a background task actually running
    for it in *this* process -- either this is a fresh process that never
    started that background task (a previous process did, and then died
    before it finished: a crash, a restart, a deploy), or this call itself
    is happening during this process's own startup, before any request has
    had a chance to dispatch a new one. Either way, `grading` is otherwise a
    dead end: it's deliberately excluded from `_ALREADY_GRADING_OR_DONE`'s
    complement (only `active`/`failed` may (re)start grading -- see
    `mark_session_grading`), so a session stuck in `grading` with no
    coordinator actually running for it would reject every future POST
    .../end with 409 forever, and GET .../report would report "grading"
    forever with no way out.

    Called once, at startup (see main.py's `_startup`), before any request
    can reach the app -- so there's no TOCTOU concern here the way there was
    for the active/failed -> grading transition: nothing else is racing this
    sweep for these particular rows at this particular moment.

    Returns the number of sessions recovered (0 in the common case where
    nothing was stuck), mainly so a caller can log it.
    """
    with _conn() as conn:
        cursor = conn.execute(
            "UPDATE practice_sessions SET status = 'failed', report_error = ? "
            "WHERE status = 'grading'",
            (message,),
        )
        return cursor.rowcount


def get_user_memory_store(user_id: str) -> str | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT memory_store_id FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        return row["memory_store_id"] if row else None


def set_user_memory_store(user_id: str, memory_store_id: str) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT INTO users (user_id, memory_store_id) VALUES (?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET memory_store_id = excluded.memory_store_id",
            (user_id, memory_store_id),
        )


def create_practice_session(session_id: str, user_id: str, scenario_id: str) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT INTO practice_sessions (id, user_id, scenario_id, created_at) "
            "VALUES (?, ?, ?, ?)",
            (session_id, user_id, scenario_id, datetime.now(timezone.utc).isoformat()),
        )


def get_practice_session(session_id: str) -> sqlite3.Row | None:
    with _conn() as conn:
        return conn.execute(
            "SELECT * FROM practice_sessions WHERE id = ?", (session_id,)
        ).fetchone()


def append_turn(session_id: str, role: str, text: str) -> None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT transcript_json FROM practice_sessions WHERE id = ?", (session_id,)
        ).fetchone()
        transcript = json.loads(row["transcript_json"])
        transcript.append({"role": role, "text": text})
        conn.execute(
            "UPDATE practice_sessions SET transcript_json = ? WHERE id = ?",
            (json.dumps(transcript), session_id),
        )


def get_transcript(session_id: str) -> list[dict]:
    with _conn() as conn:
        row = conn.execute(
            "SELECT transcript_json FROM practice_sessions WHERE id = ?", (session_id,)
        ).fetchone()
        return json.loads(row["transcript_json"]) if row else []


def remove_last_turn(session_id: str) -> None:
    """Pops the most recently appended turn off the transcript, if any.

    Used by main.py's POST .../message error handling (see `event_stream`'s
    `except` block) to roll back the user's turn when the partner-reply
    stream fails partway through -- `append_turn(session_id, "user", ...)`
    runs eagerly before the SSE generator starts, so a failure anywhere in
    the streamed reply leaves a dangling user turn with no matching
    assistant reply. Left in place, a client retry (re-sending the same
    text) would append a *second* consecutive user turn, breaking the
    strict user/assistant alternation the rest of the app assumes (e.g.
    partner.py's role mapping, the coordinator's transcript rendering).
    Popping it here restores the transcript to exactly its pre-request
    state, so a retry reproduces the normal single-user-turn-then-reply
    shape instead of compounding.

    A no-op if the session doesn't exist or its transcript is already
    empty -- defensive; in practice this is only ever called immediately
    after `append_turn` added the very turn being removed, so both should
    be impossible in normal operation.
    """
    with _conn() as conn:
        row = conn.execute(
            "SELECT transcript_json FROM practice_sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if not row:
            return
        transcript = json.loads(row["transcript_json"])
        if not transcript:
            return
        transcript.pop()
        conn.execute(
            "UPDATE practice_sessions SET transcript_json = ? WHERE id = ?",
            (json.dumps(transcript), session_id),
        )


def mark_session_grading(session_id: str) -> bool:
    """Atomic compare-and-set for the active|failed -> grading transition.

    Called synchronously in the POST .../end request handler, before the
    actual coaching run is handed off to a BackgroundTask, so the session is
    visibly "grading" (not "active") the instant the 202 response goes out.

    This is a single `UPDATE ... WHERE id = ? AND status IN ('active',
    'failed')` -- the status check and the write happen as one SQL
    statement inside sqlite3's implicit transaction (see `_conn()`), so
    there is no window between "read the status" and "write grading" for a
    second caller to land in. Two near-simultaneous callers (e.g. a client
    double-tap on POST .../end, or a retry racing an in-flight request) both
    issue this same UPDATE; sqlite serializes the two writes so they cannot
    interleave, exactly one of them matches the WHERE clause (the loser's
    row is no longer 'active'/'failed' by the time its UPDATE runs -- the
    winner already flipped it to 'grading'), and `cursor.rowcount` tells
    each caller whether *it* was the one that won.

    Returns True if this call performed the transition (the caller should
    proceed to dispatch the background grading task), False if the row
    wasn't in `active`/`failed` at the time of the UPDATE -- either because
    it never was, or because another concurrent call already won the race
    (the caller should treat this the same as the existing "already
    grading" 409 case, since -- from this caller's point of view -- it is).

    Clears any `report_error` left over from a prior failed attempt -- this
    is a fresh (re)try -- but only on the row that actually wins.
    """
    with _conn() as conn:
        cursor = conn.execute(
            "UPDATE practice_sessions SET status = 'grading', report_error = NULL "
            "WHERE id = ? AND status IN ('active', 'failed')",
            (session_id,),
        )
        return cursor.rowcount > 0


def mark_session_ended(session_id: str) -> None:
    with _conn() as conn:
        conn.execute(
            "UPDATE practice_sessions SET status = 'ended', report_error = NULL WHERE id = ?",
            (session_id,),
        )


def mark_session_failed(session_id: str, error_message: str) -> None:
    """grading -> failed. `error_message` should already be a short,
    client-safe string (see main.py's `_safe_error_message`) -- this function
    doesn't sanitize, it just stores whatever it's given."""
    with _conn() as conn:
        conn.execute(
            "UPDATE practice_sessions SET status = 'failed', report_error = ? WHERE id = ?",
            (error_message, session_id),
        )


def save_report(session_id: str, report: dict) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT INTO reports (session_id, report_json, created_at) VALUES (?, ?, ?) "
            "ON CONFLICT(session_id) DO UPDATE SET report_json = excluded.report_json",
            (session_id, json.dumps(report), datetime.now(timezone.utc).isoformat()),
        )


def get_report(session_id: str) -> dict | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT report_json FROM reports WHERE session_id = ?", (session_id,)
        ).fetchone()
        return json.loads(row["report_json"]) if row else None


def get_recent_reports(user_id: str, limit: int = 2) -> list[dict]:
    """The `limit` most recent coaching reports for a user, newest first --
    used by partner.py to build the live partner's "coach memo" (see
    ARCHITECTURE.md). Deliberately newest-first (unlike get_progress below,
    which reads oldest-first for the app's own progress-trend screen):
    only the most recent history matters for steering the next practice
    conversation, not the full trend."""
    with _conn() as conn:
        rows = conn.execute(
            """
            SELECT r.report_json
            FROM practice_sessions s
            JOIN reports r ON r.session_id = s.id
            WHERE s.user_id = ?
            ORDER BY r.created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        return [json.loads(row["report_json"]) for row in rows]


def get_progress(user_id: str) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            """
            SELECT s.id AS session_id, s.scenario_id, r.report_json, r.created_at
            FROM practice_sessions s
            JOIN reports r ON r.session_id = s.id
            WHERE s.user_id = ?
            ORDER BY r.created_at ASC
            """,
            (user_id,),
        ).fetchall()
        return [
            {
                "session_id": row["session_id"],
                "scenario_id": row["scenario_id"],
                "created_at": row["created_at"],
                "report": json.loads(row["report_json"]),
            }
            for row in rows
        ]
