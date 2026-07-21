"""Minimal sqlite-backed lesson completion storage."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any


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
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS coaching_reports (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                source_kind TEXT NOT NULL,
                transcript_json TEXT NOT NULL,
                diagnosis_json TEXT NOT NULL,
                weakest_dimension TEXT NOT NULL,
                lesson_id TEXT NOT NULL,
                recommendation_kind TEXT NOT NULL,
                practice_action TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reflections (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                subject_kind TEXT NOT NULL,
                subject_id TEXT NOT NULL,
                outcome TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS review_completions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                lesson_id TEXT NOT NULL,
                completed_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS onboarding (
                user_id TEXT PRIMARY KEY,
                goal TEXT NOT NULL,
                context TEXT NOT NULL,
                baseline_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        return connection

    def save_onboarding(
        self,
        *,
        user_id: str,
        goal: str,
        context: str,
        baseline: dict[str, int],
    ) -> str:
        """Persist a user's latest deterministic onboarding choices."""
        created_at = datetime.now(UTC).isoformat()
        with closing(self._connect()) as connection:
            with connection:
                connection.execute(
                    """
                    INSERT OR REPLACE INTO onboarding
                    (user_id, goal, context, baseline_json, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (user_id, goal, context, json.dumps(baseline), created_at),
                )
        return created_at

    def onboarding(self, user_id: str) -> dict[str, Any] | None:
        """Return a user's stored onboarding choices, if they have any."""
        with closing(self._connect()) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                """
                SELECT goal, context, baseline_json, created_at
                FROM onboarding WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["baseline"] = json.loads(result.pop("baseline_json"))
        return result

    def completed_lesson_ids(self, user_id: str) -> set[str]:
        with closing(self._connect()) as connection:
            with connection:
                rows = connection.execute(
                    "SELECT lesson_id FROM lesson_completions WHERE user_id = ?", (user_id,)
                ).fetchall()
        return {row[0] for row in rows}

    def activity_timestamps(self, user_id: str) -> dict[str, list[Any]]:
        """Return raw persisted timestamps used to derive daily activity."""
        with closing(self._connect()) as connection:
            with connection:
                lesson_rows = connection.execute(
                    """
                    SELECT lesson_id, completed_at FROM lesson_completions
                    WHERE user_id = ?
                    """,
                    (user_id,),
                ).fetchall()
                report_rows = connection.execute(
                    """
                    SELECT created_at FROM coaching_reports WHERE user_id = ?
                    """,
                    (user_id,),
                ).fetchall()
                review_rows = connection.execute(
                    """
                    SELECT lesson_id, completed_at FROM review_completions
                    WHERE user_id = ?
                    """,
                    (user_id,),
                ).fetchall()
        return {
            "lesson_completions": [(row[0], row[1]) for row in lesson_rows],
            "coaching_reports": [row[0] for row in report_rows],
            "review_completions": [(row[0], row[1]) for row in review_rows],
        }

    def record_completion(self, user_id: str, lesson_id: str) -> None:
        with closing(self._connect()) as connection:
            with connection:
                connection.execute(
                    "INSERT OR IGNORE INTO lesson_completions (user_id, lesson_id) VALUES (?, ?)",
                    (user_id, lesson_id),
                )

    def record_review(self, user_id: str, lesson_id: str) -> str:
        """Persist a repeatable review completion and return its UTC timestamp."""
        created_at = datetime.now(UTC).isoformat()
        with closing(self._connect()) as connection:
            with connection:
                connection.execute(
                    """
                    INSERT INTO review_completions (user_id, lesson_id, completed_at)
                    VALUES (?, ?, ?)
                    """,
                    (user_id, lesson_id, created_at),
                )
        return created_at

    def review_timestamps(self, user_id: str) -> list[tuple[str, str]]:
        """Return raw review timestamps for deterministic scheduling."""
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT lesson_id, completed_at FROM review_completions
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchall()
        return [(row[0], row[1]) for row in rows]

    def save_coaching_report(
        self,
        *,
        report_id: str,
        user_id: str,
        transcript: dict[str, Any],
        diagnosis: dict[str, Any],
        weakest_dimension: str,
        lesson_id: str,
        recommendation_kind: str,
        practice_action: str,
    ) -> str:
        """Persist the report and its transcript as one sqlite record."""
        created_at = datetime.now(UTC).isoformat()
        with closing(self._connect()) as connection:
            with connection:
                connection.execute(
                    """
                    INSERT INTO coaching_reports
                    (id, user_id, created_at, source_kind, transcript_json, diagnosis_json,
                     weakest_dimension, lesson_id, recommendation_kind, practice_action)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        report_id,
                        user_id,
                        created_at,
                        transcript["source_kind"],
                        json.dumps(transcript, ensure_ascii=False),
                        json.dumps(diagnosis, ensure_ascii=False),
                        weakest_dimension,
                        lesson_id,
                        recommendation_kind,
                        practice_action,
                    ),
                )
        return created_at

    def coaching_report(self, report_id: str, user_id: str) -> dict[str, Any] | None:
        with closing(self._connect()) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                "SELECT * FROM coaching_reports WHERE id = ? AND user_id = ?", (report_id, user_id)
            ).fetchone()
        return dict(row) if row is not None else None

    def coaching_report_summaries(self, user_id: str) -> list[dict[str, str]]:
        with closing(self._connect()) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT id, created_at, source_kind, weakest_dimension, lesson_id
                FROM coaching_reports WHERE user_id = ?
                ORDER BY created_at DESC, id DESC
                """,
                (user_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def coaching_report_rows(self, user_id: str) -> list[dict[str, Any]]:
        """Return raw persisted fields needed for deterministic profile aggregation."""
        with closing(self._connect()) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT id, created_at, weakest_dimension, lesson_id,
                       recommendation_kind, diagnosis_json
                FROM coaching_reports WHERE user_id = ?
                ORDER BY created_at ASC, id ASC
                """,
                (user_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def save_reflection(
        self,
        *,
        reflection_id: str,
        user_id: str,
        subject_kind: str,
        subject_id: str,
        outcome: str,
        note: str,
    ) -> str:
        """Persist a user-owned reflection and return its UTC creation timestamp."""
        created_at = datetime.now(UTC).isoformat()
        with closing(self._connect()) as connection:
            with connection:
                connection.execute(
                    """
                    INSERT INTO reflections
                    (id, user_id, subject_kind, subject_id, outcome, note, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (reflection_id, user_id, subject_kind, subject_id, outcome, note, created_at),
                )
        return created_at

    def reflections(self, user_id: str) -> list[dict[str, str]]:
        """Return a user's reflections newest first."""
        with closing(self._connect()) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT id, subject_kind, subject_id, outcome, note, created_at
                FROM reflections WHERE user_id = ?
                ORDER BY created_at DESC, id DESC
                """,
                (user_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def delete_coaching_report(self, report_id: str, user_id: str) -> bool:
        """Delete the single record containing both report and transcript atomically."""
        with closing(self._connect()) as connection:
            with connection:
                cursor = connection.execute(
                    "DELETE FROM coaching_reports WHERE id = ? AND user_id = ?", (report_id, user_id)
                )
        return cursor.rowcount == 1
