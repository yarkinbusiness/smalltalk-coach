"""Deterministic longitudinal coaching profile aggregation."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from typing import Any, Iterable, Mapping

from .content import Curriculum
from .diagnosis import DIMENSIONS
from .streak import parse_activity_timestamp


def _is_score(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= 5


def _diagnosis(value: Any) -> dict[str, Any] | None:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (TypeError, ValueError):
            return None
    return value if isinstance(value, dict) else None


def _valid_report(row: Mapping[str, Any]) -> tuple[datetime, dict[str, Any]] | None:
    if not isinstance(row, Mapping):
        return None
    report_id = row.get("id")
    created_at = row.get("created_at")
    weakest_dimension = row.get("weakest_dimension")
    lesson_id = row.get("lesson_id")
    recommendation_kind = row.get("recommendation_kind")
    parsed_created_at = parse_activity_timestamp(created_at)
    diagnosis = _diagnosis(row.get("diagnosis_json"))
    if (
        not isinstance(report_id, str)
        or not isinstance(created_at, str)
        or parsed_created_at is None
        or weakest_dimension not in DIMENSIONS
        or not isinstance(lesson_id, str)
        or not isinstance(recommendation_kind, str)
        or diagnosis is None
        or diagnosis.get("mode") not in {"stimulus_only", "with_user_reply"}
        or "dimensions" not in diagnosis
    ):
        return None

    dimensions = diagnosis["dimensions"]
    if diagnosis["mode"] == "stimulus_only" and dimensions is not None:
        return None
    if diagnosis["mode"] == "with_user_reply" and dimensions is None:
        return None
    if dimensions is not None:
        if not isinstance(dimensions, dict):
            return None
        for dimension in DIMENSIONS:
            value = dimensions.get(dimension)
            if not isinstance(value, dict) or not _is_score(value.get("score")):
                return None

    return parsed_created_at, {
        "id": report_id,
        "created_at": created_at,
        "weakest_dimension": weakest_dimension,
        "lesson_id": lesson_id,
        "dimensions": dimensions,
    }


def build_profile(
    reports: Iterable[Mapping[str, Any]],
    completed_lesson_ids: set[str],
    curriculum: Curriculum,
) -> dict[str, object]:
    """Aggregate valid persisted reports into the stable profile response shape."""
    valid_reports = [valid for row in reports if (valid := _valid_report(row)) is not None]
    valid_reports.sort(key=lambda item: (item[0], item[1]["id"]))

    dimensions: dict[str, dict[str, object]] = {
        dimension: {"scores": [], "flagged_count": 0} for dimension in DIMENSIONS
    }
    flagged_counts = Counter(report["weakest_dimension"] for _, report in valid_reports)
    for dimension in DIMENSIONS:
        dimensions[dimension]["flagged_count"] = flagged_counts[dimension]

    for _, report in valid_reports:
        report_dimensions = report["dimensions"]
        if report_dimensions is None:
            continue
        for dimension in DIMENSIONS:
            scores = dimensions[dimension]["scores"]
            assert isinstance(scores, list)
            scores.append({
                "report_id": report["id"],
                "created_at": report["created_at"],
                "score": report_dimensions[dimension]["score"],
            })
    for dimension in DIMENSIONS:
        scores = dimensions[dimension]["scores"]
        assert isinstance(scores, list)
        dimensions[dimension]["scores"] = scores[-10:]

    recent_reports = valid_reports[-5:]
    recent_counts = Counter(report["weakest_dimension"] for _, report in recent_reports)
    recurring_weakness = next(
        (
            {"dimension": dimension, "flagged_recent": recent_counts[dimension], "window": len(recent_reports)}
            for dimension in DIMENSIONS
            if len(valid_reports) >= 3 and recent_counts[dimension] >= 3
        ),
        None,
    )

    recommendations: dict[str, tuple[datetime, dict[str, Any]]] = {}
    for created_at, report in valid_reports:
        lesson_id = report["lesson_id"]
        if lesson_id in completed_lesson_ids or lesson_id not in curriculum.lessons_by_id:
            continue
        previous = recommendations.get(lesson_id)
        if previous is None or (created_at, report["id"]) > (previous[0], previous[1]["id"]):
            recommendations[lesson_id] = (created_at, report)

    recommended_not_taken = [
        {
            "lesson_id": lesson_id,
            "title": curriculum.lessons_by_id[lesson_id]["title"],
            "recommended_at": report["created_at"],
        }
        for lesson_id, (_, report) in sorted(
            recommendations.items(), key=lambda item: (item[1][0], item[1][1]["id"]), reverse=True
        )
    ]

    return {
        "report_count": len(valid_reports),
        "dimensions": dimensions,
        "recurring_weakness": recurring_weakness,
        "lessons": {
            "completed_count": len(completed_lesson_ids),
            "recommended_not_taken": recommended_not_taken,
        },
    }
