"""Deterministic, timezone-aware spaced-review scheduling."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Iterable
from zoneinfo import ZoneInfo

from .content import Curriculum


_INTERVALS = (3, 7, 21)


def build_review_queue(
    lesson_completions: Iterable[tuple[str, datetime]],
    review_completions: Iterable[tuple[str, datetime]],
    curriculum: Curriculum,
    priority_dimension: str | None,
    timezone: ZoneInfo,
    now: datetime,
) -> list[dict[str, str | int]]:
    """Return due reviews in priority, overdue, then curriculum-path order.

    The gap after a completion and ``r`` reviews is ``_INTERVALS[min(r, 2)]``.
    Dates are deliberately evaluated in the user's timezone, rather than by
    elapsed 24-hour windows.
    """
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")

    today = now.astimezone(timezone).date()
    completed_by_lesson: dict[str, list[datetime]] = defaultdict(list)
    reviews_by_lesson: dict[str, list[datetime]] = defaultdict(list)
    known_ids = set(curriculum.lessons_by_id)

    for lesson_id, completed_at in lesson_completions:
        if (
            lesson_id in known_ids
            and completed_at.tzinfo is not None
            and completed_at.astimezone(timezone).date() <= today
        ):
            completed_by_lesson[lesson_id].append(completed_at)
    for lesson_id, reviewed_at in review_completions:
        if (
            lesson_id in completed_by_lesson
            and reviewed_at.tzinfo is not None
            and reviewed_at.astimezone(timezone).date() <= today
        ):
            reviews_by_lesson[lesson_id].append(reviewed_at)

    due: list[tuple[bool, int, int, dict[str, str | int]]] = []
    for path_index, lesson in enumerate(curriculum.lessons):
        lesson_id = lesson["id"]
        completions = completed_by_lesson.get(lesson_id)
        if not completions:
            continue
        reviews = reviews_by_lesson[lesson_id]
        most_recent = max((*completions, *reviews))
        due_date = most_recent.astimezone(timezone).date() + timedelta(
            days=_INTERVALS[min(len(reviews), len(_INTERVALS) - 1)]
        )
        if today < due_date:
            continue
        days_overdue = (today - due_date).days
        dimension = next(
            (value for value in lesson["dimensions"] if value == priority_dimension),
            lesson["dimensions"][0],
        )
        item: dict[str, str | int] = {
            "lesson_id": lesson_id,
            "title": lesson["title"],
            "unit_id": f"u{lesson['unit']}",
            "days_overdue": days_overdue,
            "dimension": dimension,
        }
        due.append((priority_dimension in lesson["dimensions"], days_overdue, path_index, item))

    due.sort(key=lambda item: (not item[0], -item[1], item[2]))
    return [item[3] for item in due]
