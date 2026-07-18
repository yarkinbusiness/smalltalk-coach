from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import pytest
from fastapi.testclient import TestClient

from backend.app.content import ContentValidationError, load_curriculum
from backend.app.main import create_app


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
    }
    assert {name: len(ids) for name, ids in curriculum.routing.items()} == {
        "warmth": 5,
        "curiosity": 6,
        "reciprocity": 6,
        "flow": 7,
    }
    assert curriculum.content["l01-first-hello"]["title"] == "First hello"


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
