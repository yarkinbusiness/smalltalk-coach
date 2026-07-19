"""Ephemeral, thread-safe screenshot coaching jobs.

Jobs are intentionally in-memory only. A process restart loses the store, so
in-flight screenshot work cannot be recovered and callers must re-upload.
Raw image data is never placed on a job record.
"""

from __future__ import annotations

from datetime import UTC, datetime
from threading import Lock
from typing import Any
import uuid


class CoachingJobStore:
    """Keep only screenshot job metadata and final references in process memory."""

    def __init__(self) -> None:
        self._jobs: dict[str, dict[str, Any]] = {}
        self._lock = Lock()

    def create(self, user_id: str) -> dict[str, Any]:
        job = {
            "id": f"cj_{uuid.uuid4().hex}",
            "user_id": user_id,
            "status": "processing",
            "created_at": datetime.now(UTC).isoformat(),
        }
        with self._lock:
            self._jobs[job["id"]] = job
        return dict(job)

    def complete_report(self, job_id: str, report_id: str) -> None:
        with self._lock:
            self._jobs[job_id] = self._jobs[job_id] | {
                "status": "completed", "report_id": report_id,
            }

    def complete_safety(self, job_id: str, category: str, guidance: str) -> None:
        with self._lock:
            self._jobs[job_id] = self._jobs[job_id] | {
                "status": "safety_guidance", "category": category, "guidance": guidance,
            }

    def fail(self, job_id: str, *, status_code: int, detail: str) -> None:
        with self._lock:
            self._jobs[job_id] = self._jobs[job_id] | {
                "status": "failed", "status_code": status_code, "detail": detail,
            }

    def get(self, job_id: str, user_id: str) -> dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None or job["user_id"] != user_id:
                return None
            return dict(job)
