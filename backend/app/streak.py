"""Deterministic, timezone-aware daily streak and freeze computation."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from typing import Iterable, Mapping
from zoneinfo import ZoneInfo


def parse_activity_timestamp(value: str) -> datetime | None:
    """Parse either timestamp format persisted by the application as UTC.

    SQLite lesson completions have no offset marker, while coaching reports
    are Python ISO-8601 timestamps with an explicit UTC offset.
    """
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
    except (TypeError, ValueError):
        pass
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(UTC)


def compute_streak(
    lesson_completions: Iterable[tuple[str, datetime]],
    coaching_reports: Iterable[datetime],
    unit_lessons: Mapping[object, Iterable[str]],
    timezone: ZoneInfo,
    now: datetime,
    review_completions: Iterable[datetime] = (),
) -> dict[str, int | bool]:
    """Replay activity history into a current local-day streak state."""
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")

    today = now.astimezone(timezone).date()
    activity_days: set[date] = set()
    completed_at: dict[str, list[datetime]] = defaultdict(list)

    for lesson_id, completed in lesson_completions:
        if completed.tzinfo is None:
            continue
        local_day = completed.astimezone(timezone).date()
        if local_day <= today:
            activity_days.add(local_day)
            completed_at[lesson_id].append(completed)
    for created in coaching_reports:
        if created.tzinfo is None:
            continue
        local_day = created.astimezone(timezone).date()
        if local_day <= today:
            activity_days.add(local_day)
    for reviewed in review_completions:
        if reviewed.tzinfo is None:
            continue
        local_day = reviewed.astimezone(timezone).date()
        if local_day <= today:
            activity_days.add(local_day)

    if not activity_days:
        return {
            "streak_days": 0,
            "active_today": False,
            "freezes": 0,
            "freezes_earned_total": 0,
        }

    earn_days: dict[date, int] = defaultdict(int)
    for lesson_ids in unit_lessons.values():
        lesson_ids = tuple(lesson_ids)
        if lesson_ids and all(completed_at.get(lesson_id) for lesson_id in lesson_ids):
            last_completion = max(
                completed
                for lesson_id in lesson_ids
                for completed in completed_at[lesson_id]
            )
            earn_days[last_completion.astimezone(timezone).date()] += 1

    streak_days = 0
    freezes = 0
    freezes_earned_total = 0
    day = min(activity_days)
    while day <= today:
        if day in activity_days:
            streak_days += 1
            for _ in range(earn_days[day]):
                freezes_earned_total += 1
                freezes = min(2, freezes + 1)
        elif day < today:
            if streak_days and freezes:
                freezes -= 1
            else:
                streak_days = 0
        day += timedelta(days=1)

    return {
        "streak_days": streak_days,
        "active_today": today in activity_days,
        "freezes": freezes,
        "freezes_earned_total": freezes_earned_total,
    }
