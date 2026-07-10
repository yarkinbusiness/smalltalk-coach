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


def init_db() -> None:
    with _conn() as conn:
        conn.executescript(SCHEMA)


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


def mark_session_ended(session_id: str) -> None:
    with _conn() as conn:
        conn.execute(
            "UPDATE practice_sessions SET status = 'ended' WHERE id = ?", (session_id,)
        )


def save_report(session_id: str, report: dict) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT INTO reports (session_id, report_json, created_at) VALUES (?, ?, ?) "
            "ON CONFLICT(session_id) DO UPDATE SET report_json = excluded.report_json",
            (session_id, json.dumps(report), datetime.now(timezone.utc).isoformat()),
        )


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
