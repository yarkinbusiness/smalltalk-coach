from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.content import Curriculum, load_curriculum
from backend.app.diagnosis import DIMENSIONS
from backend.app.main import create_app
from backend.app.profile import build_profile


REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "content" / "lesson_path.json"
LESSONS_DIR = REPO_ROOT / "content" / "lessons"


def _curriculum() -> Curriculum:
    return load_curriculum(MANIFEST_PATH, LESSONS_DIR)


def _diagnosis(scores: dict[str, int] | None) -> dict[str, object]:
    return {
        "mode": "with_user_reply" if scores is not None else "stimulus_only",
        "dimensions": (
            {dimension: {"score": score} for dimension, score in scores.items()}
            if scores is not None else None
        ),
    }


def _row(
    report_id: str,
    created_at: str,
    *,
    weakest_dimension: str = "reciprocity",
    lesson_id: str = "l04-answer-and-return",
    scores: dict[str, int] | None = None,
) -> dict[str, str]:
    return {
        "id": report_id,
        "created_at": created_at,
        "weakest_dimension": weakest_dimension,
        "lesson_id": lesson_id,
        "recommendation_kind": "new",
        "diagnosis_json": json.dumps(_diagnosis(scores)),
    }


def _scores(value: int = 3) -> dict[str, int]:
    return {dimension: value for dimension in DIMENSIONS}


def _client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(
        manifest_path=MANIFEST_PATH,
        lessons_dir=LESSONS_DIR,
        database_path=tmp_path / "progress.db",
    ))


def _save_report(
    client: TestClient,
    report_id: str,
    diagnosis: dict[str, object],
    *,
    weakest_dimension: str = "reciprocity",
    lesson_id: str = "l04-answer-and-return",
) -> str:
    return client.app.state.progress_store.save_coaching_report(
        report_id=report_id,
        user_id="maya",
        transcript={"source_kind": "text"},
        diagnosis=diagnosis,
        weakest_dimension=weakest_dimension,
        lesson_id=lesson_id,
        recommendation_kind="new",
        practice_action="Practice.",
    )


def test_empty_history_has_the_exact_profile_shape() -> None:
    assert build_profile([], set(), _curriculum()) == {
        "report_count": 0,
        "dimensions": {
            dimension: {"scores": [], "flagged_count": 0} for dimension in DIMENSIONS
        },
        "recurring_weakness": None,
        "lessons": {"completed_count": 0, "recommended_not_taken": []},
    }


def test_stimulus_only_report_is_flagged_without_scores() -> None:
    profile = build_profile([
        _row("one", "2026-01-01T12:00:00+00:00", weakest_dimension="curiosity",
             lesson_id="l03-easy-first-question"),
    ], set(), _curriculum())

    assert profile["report_count"] == 1
    assert profile["dimensions"] == {
        "warmth": {"scores": [], "flagged_count": 0},
        "curiosity": {"scores": [], "flagged_count": 1},
        "reciprocity": {"scores": [], "flagged_count": 0},
        "flow": {"scores": [], "flagged_count": 0},
    }
    assert profile["recurring_weakness"] is None
    assert profile["lessons"]["recommended_not_taken"] == [{
        "lesson_id": "l03-easy-first-question",
        "title": "Ask an easy first question",
        "recommended_at": "2026-01-01T12:00:00+00:00",
    }]


def test_scored_history_is_chronological_and_capped_at_ten() -> None:
    reports = [
        _row(
            f"report-{index:02}", f"2026-01-{index + 1:02}T12:00:00+00:00",
            scores=_scores((index % 5) + 1),
        )
        for index in range(12)
    ]
    reports.append(_row("unscored", "2026-01-13T12:00:00+00:00"))
    profile = build_profile(list(reversed(reports)), set(), _curriculum())

    for dimension in DIMENSIONS:
        scores = profile["dimensions"][dimension]["scores"]
        assert [item["report_id"] for item in scores] == [
            f"report-{index:02}" for index in range(2, 12)
        ]
        assert [item["score"] for item in scores] == [(index % 5) + 1 for index in range(2, 12)]


def test_recurring_weakness_uses_only_the_most_recent_five_reports() -> None:
    base = "2026-02-{:02}T12:00:00+00:00"
    recurring = [
        _row(f"recent-{index}", base.format(index + 1), weakest_dimension=dimension)
        for index, dimension in enumerate(("warmth", "reciprocity", "reciprocity", "flow", "reciprocity"))
    ]
    assert build_profile(recurring, set(), _curriculum())["recurring_weakness"] == {
        "dimension": "reciprocity", "flagged_recent": 3, "window": 5,
    }

    no_recent_recurrence = [
        _row(f"old-{index}", base.format(index + 1), weakest_dimension="reciprocity")
        for index in range(3)
    ] + [
        _row(f"new-{index}", base.format(index + 4), weakest_dimension=dimension)
        for index, dimension in enumerate(("warmth", "reciprocity", "flow", "reciprocity", "warmth"))
    ]
    assert build_profile(no_recent_recurrence, set(), _curriculum())["recurring_weakness"] is None


def test_recommendations_exclude_completed_dedupe_and_order_defensively() -> None:
    profile = build_profile([
        _row("old-l04", "2026-01-01T12:00:00+00:00", lesson_id="l04-answer-and-return"),
        _row("complete", "2026-01-02T12:00:00+00:00", lesson_id="l03-easy-first-question"),
        _row("new-l04", "2026-01-03T12:00:00+00:00", lesson_id="l04-answer-and-return"),
        _row("l05", "2026-01-04T12:00:00+00:00", lesson_id="l05-show-you-heard"),
        _row("unknown", "2026-01-05T12:00:00+00:00", lesson_id="not-a-lesson"),
    ], {"l03-easy-first-question"}, _curriculum())

    assert profile["lessons"] == {
        "completed_count": 1,
        "recommended_not_taken": [
            {
                "lesson_id": "l05-show-you-heard",
                "title": "Show you heard them",
                "recommended_at": "2026-01-04T12:00:00+00:00",
            },
            {
                "lesson_id": "l04-answer-and-return",
                "title": "Answer, then return",
                "recommended_at": "2026-01-03T12:00:00+00:00",
            },
        ],
    }


def test_endpoint_skips_malformed_diagnosis_and_returns_contract(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        created_at = _save_report(
            client, "scored", _diagnosis(_scores(3)), weakest_dimension="reciprocity"
        )
        _save_report(client, "malformed", _diagnosis(_scores(2)), weakest_dimension="flow")
        store = client.app.state.progress_store
        with store._connect() as connection:
            connection.execute(
                "UPDATE coaching_reports SET diagnosis_json = ? WHERE id = ?",
                ("{malformed", "malformed"),
            )
            connection.commit()
        response = client.get("/users/maya/profile")

    assert response.status_code == 200
    assert response.json() == {
        "report_count": 1,
        "dimensions": {
            "warmth": {"scores": [{"report_id": "scored", "created_at": created_at, "score": 3}], "flagged_count": 0},
            "curiosity": {"scores": [{"report_id": "scored", "created_at": created_at, "score": 3}], "flagged_count": 0},
            "reciprocity": {"scores": [{"report_id": "scored", "created_at": created_at, "score": 3}], "flagged_count": 1},
            "flow": {"scores": [{"report_id": "scored", "created_at": created_at, "score": 3}], "flagged_count": 0},
        },
        "recurring_weakness": None,
        "lessons": {
            "completed_count": 0,
            "recommended_not_taken": [{
                "lesson_id": "l04-answer-and-return",
                "title": "Answer, then return",
                "recommended_at": created_at,
            }],
        },
    }
