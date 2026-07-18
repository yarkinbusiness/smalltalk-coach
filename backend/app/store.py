"""Minimal sqlite-backed lesson completion storage."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path


class ProgressStore:
    """Store completed lesson ids per caller-supplied user id."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path)
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS lesson_completions (
                user_id TEXT NOT NULL,
                lesson_id TEXT NOT NULL,
                completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, lesson_id)
            )
            """
        )
        return connection

    def completed_lesson_ids(self, user_id: str) -> set[str]:
        with closing(self._connect()) as connection:
            with connection:
                rows = connection.execute(
                    "SELECT lesson_id FROM lesson_completions WHERE user_id = ?", (user_id,)
                ).fetchall()
        return {row[0] for row in rows}

    def record_completion(self, user_id: str, lesson_id: str) -> None:
        with closing(self._connect()) as connection:
            with connection:
                connection.execute(
                    "INSERT OR IGNORE INTO lesson_completions (user_id, lesson_id) VALUES (?, ?)",
                    (user_id, lesson_id),
                )
