from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Callable

import pytest
from fastapi.testclient import TestClient

from backend.app.content import ContentValidationError, load_curriculum
from backend.app.main import _shuffled_lesson_content, create_app


REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "content" / "lesson_path.json"
LESSONS_DIR = REPO_ROOT / "content" / "lessons"


def test_real_manifest_is_consistent_and_authored_lessons_load() -> None:
    curriculum = load_curriculum(MANIFEST_PATH, LESSONS_DIR)

    assert len(curriculum.lessons) == 12
    assert set(curriculum.content) == {
        "l01-first-hello",
        "l02-use-the-setting",
        "l03-easy-first-question",
        "l04-answer-and-return",
        "l05-show-you-heard",
        "l06-follow-the-thread",
        "l07-share-and-make-space",
        "l08-handle-the-pause",
        "l09-read-the-room",
        "l10-build-on-common-ground",
        "l11-end-warmly",
        "l12-make-continuity-easy",
    }
    assert {name: len(ids) for name, ids in curriculum.routing.items()} == {
        "warmth": 5,
        "curiosity": 6,
        "reciprocity": 6,
        "flow": 7,
    }
    assert curriculum.content["l01-first-hello"]["title"] == "First hello"


def test_real_lessons_vary_correct_choice_answer_positions() -> None:
    curriculum = load_curriculum(MANIFEST_PATH, LESSONS_DIR)

    for lesson_id, lesson in curriculum.content.items():
        choice_parts = [
            lesson["exercise"],
            *(part for part in lesson["completion_check"]["parts"] if part["kind"] == "choice"),
        ]
        if len(choice_parts) >= 2:
            correct_option_indices = {
                part["correct_option_index"] for part in choice_parts
            }
            assert len(correct_option_indices) >= 2, (
                f"{lesson_id} has every correct choice answer at one position"
            )


def test_shuffled_lesson_content_is_deterministic() -> None:
    curriculum = load_curriculum(MANIFEST_PATH, LESSONS_DIR)
    lesson_id = "l04-answer-and-return"
    lesson = curriculum.content[lesson_id]

    first = _shuffled_lesson_content(lesson, "maya", lesson_id, 2)
    second = _shuffled_lesson_content(lesson, "maya", lesson_id, 2)

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_shuffled_lesson_content_varies_across_attempts() -> None:
    curriculum = load_curriculum(MANIFEST_PATH, LESSONS_DIR)
    lesson_id = "l04-answer-and-return"
    lesson = curriculum.content[lesson_id]
    shuffled = [
        _shuffled_lesson_content(lesson, "maya", lesson_id, attempt_index)
        for attempt_index in range(5)
    ]

    choice_orders = [
        [
            (part["options"], part["correct_option_index"])
            for part in item["completion_check"]["parts"]
            if part["kind"] == "choice"
        ]
        for item in shuffled
    ]
    assert any(order != choice_orders[0] for order in choice_orders[1:])


def test_shuffled_lesson_content_never_mutates_loaded_curriculum() -> None:
    curriculum = load_curriculum(MANIFEST_PATH, LESSONS_DIR)
    lesson_id = "l04-answer-and-return"
    lesson = curriculum.content[lesson_id]
    snapshot = deepcopy(lesson)

    for user_id in ("maya", "noah", "ava"):
        for attempt_index in range(5):
            shuffled = _shuffled_lesson_content(lesson, user_id, lesson_id, attempt_index)
            assert shuffled is not lesson
            assert shuffled["completion_check"] is not lesson["completion_check"]
            assert shuffled["completion_check"]["parts"] is not lesson["completion_check"]["parts"]
            for original_part, shuffled_part in zip(
                lesson["completion_check"]["parts"],
                shuffled["completion_check"]["parts"],
                strict=True,
            ):
                if original_part["kind"] == "choice":
                    assert shuffled_part is not original_part

    assert curriculum.content[lesson_id] == snapshot


def test_shuffled_lesson_content_keeps_option_text_and_feedback_paired() -> None:
    curriculum = load_curriculum(MANIFEST_PATH, LESSONS_DIR)
    lesson_id = "l04-answer-and-return"
    lesson = curriculum.content[lesson_id]
    shuffled = _shuffled_lesson_content(lesson, "maya", lesson_id, 3)

    for original_part, shuffled_part in zip(
        lesson["completion_check"]["parts"], shuffled["completion_check"]["parts"], strict=True
    ):
        if original_part["kind"] != "choice":
            continue
        original_pairs = {
            (option["text"], option["feedback"])
            for option in original_part["options"]
        }
        shuffled_pairs = {
            (option["text"], option["feedback"])
            for option in shuffled_part["options"]
        }
        assert shuffled_pairs == original_pairs


Mutation = Callable[[dict[str, Any]], None]


def _write_fixture(tmp_path: Path, mutate: Mutation) -> tuple[Path, Path]:
    manifest_path = tmp_path / "lesson_path.json"
    manifest_path.write_text(MANIFEST_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    lessons_dir = tmp_path / "lessons"
    lessons_dir.mkdir()
    lesson = json.loads((LESSONS_DIR / "l01-first-hello.json").read_text(encoding="utf-8"))
    mutate(lesson)
    (lessons_dir / "l01-first-hello.json").write_text(
        json.dumps(lesson), encoding="utf-8"
    )
    return manifest_path, lessons_dir


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda lesson: lesson.__setitem__("id", "l02-use-the-setting"), "match its filename"),
        (lambda lesson: lesson.pop("concept_intro"), "missing required field concept_intro"),
        (
            lambda lesson: lesson["exercise"].__setitem__("correct_option_index", 99),
            "must be an in-range integer",
        ),
        (lambda lesson: lesson.__setitem__("dimensions", ["warmth"]), "contradict manifest routing"),
        (
            lambda lesson: lesson["practice"].__setitem__("type", "Draft-then-compare"),
            "does not match manifest practice_type",
        ),
    ],
)
def test_invalid_lesson_content_is_rejected(
    tmp_path: Path, mutate: Mutation, message: str
) -> None:
    manifest_path, lessons_dir = _write_fixture(tmp_path, mutate)

    with pytest.raises(ContentValidationError, match=message):
        load_curriculum(manifest_path, lessons_dir)


def test_invalid_existing_content_fails_app_startup(tmp_path: Path) -> None:
    manifest_path, lessons_dir = _write_fixture(
        tmp_path, lambda lesson: lesson.pop("completion_check")
    )
    app = create_app(
        manifest_path=manifest_path,
        lessons_dir=lessons_dir,
        database_path=tmp_path / "progress.db",
    )

    with pytest.raises(ContentValidationError, match="missing required field completion_check"):
        with TestClient(app):
            pass
