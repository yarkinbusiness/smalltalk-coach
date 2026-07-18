"""Deterministic diagnosis-to-lesson routing; the model never chooses a lesson."""

from __future__ import annotations

from typing import Any

from .content import Curriculum


DIMENSION_ORDER = ("warmth", "curiosity", "reciprocity", "flow")


class RoutingError(ValueError):
    """Raised for a broken routing configuration."""


def route_diagnosis(
    diagnosis: dict[str, Any], curriculum: Curriculum, completed_lesson_ids: set[str]
) -> dict[str, Any]:
    """Choose the lowest score, fixed-order tie-breaker, then earliest route."""
    dimensions = diagnosis["dimensions"]
    weakest_dimension = min(DIMENSION_ORDER, key=lambda name: dimensions[name]["score"])
    routing_row = curriculum.routing.get(weakest_dimension)
    if not routing_row:
        raise RoutingError("missing routing row")
    lesson_id = next((item for item in routing_row if item not in completed_lesson_ids), routing_row[0])
    lesson = curriculum.lessons_by_id.get(lesson_id)
    if lesson is None:
        raise RoutingError("missing routed lesson")
    return {
        "weakest_dimension": weakest_dimension,
        "selection_reason": "lowest_score",
        "lesson": {
            "id": lesson["id"],
            "title": lesson["title"],
            "concept": lesson["concept"],
            "skill_objective": lesson["skill_objective"],
            "recommendation_kind": "new" if lesson_id not in completed_lesson_ids else "review",
        },
    }
