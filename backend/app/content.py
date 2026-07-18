"""Load and validate the locked lesson path and authored lesson files."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ALLOWED_DIMENSIONS = frozenset({"warmth", "curiosity", "reciprocity", "flow"})
METADATA_FIELDS = (
    "id",
    "title",
    "unit",
    "sequence",
    "concept",
    "skill_objective",
    "dimensions",
)
CONTENT_BLOCKS = (
    "concept_intro",
    "example",
    "responses",
    "exercise",
    "practice",
    "completion_check",
)
PRACTICE_TYPES = {
    "l01-first-hello": "Short roleplay",
    "l02-use-the-setting": "Choose-the-better-reply",
    "l03-easy-first-question": "Draft-then-compare",
    "l04-answer-and-return": "Short roleplay",
    "l05-show-you-heard": "Choose-the-better-reply",
    "l06-follow-the-thread": "Short roleplay",
    "l07-share-and-make-space": "Draft-then-compare",
    "l08-handle-the-pause": "Choose-the-next-move",
    "l09-read-the-room": "Cue-sort exercise",
    "l10-build-on-common-ground": "Short roleplay",
    "l11-end-warmly": "Draft-then-compare",
    "l12-make-continuity-easy": "Short roleplay",
}


class ContentValidationError(ValueError):
    """Raised when a manifest or lesson file violates the locked model."""


@dataclass(frozen=True)
class Curriculum:
    """The validated manifest and authored content keyed by lesson id."""

    lessons: tuple[dict[str, Any], ...]
    routing: dict[str, tuple[str, ...]]
    content: dict[str, dict[str, Any]]

    @property
    def lessons_by_id(self) -> dict[str, dict[str, Any]]:
        return {lesson["id"]: lesson for lesson in self.lessons}


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _require_object(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContentValidationError(f"{context} must be a JSON object")
    return value


def _require_string(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContentValidationError(f"{context} must be a non-empty string")
    return value


def _require_index(value: Any, options: list[Any], context: str) -> int:
    if not _is_int(value) or not 0 <= value < len(options):
        raise ContentValidationError(f"{context} must be an in-range integer")
    return value


def _require_options(value: Any, context: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not 2 <= len(value) <= 4:
        raise ContentValidationError(f"{context} must contain two to four options")
    options: list[dict[str, Any]] = []
    for index, option in enumerate(value):
        option_object = _require_object(option, f"{context}[{index}]")
        _require_string(option_object.get("text"), f"{context}[{index}].text")
        _require_string(option_object.get("feedback"), f"{context}[{index}].feedback")
        options.append(option_object)
    return options


def _validate_manifest(manifest: Any) -> tuple[tuple[dict[str, Any], ...], dict[str, tuple[str, ...]]]:
    data = _require_object(manifest, "lesson manifest")
    if data.get("schema_version") != 1:
        raise ContentValidationError("lesson manifest schema_version must be 1")

    raw_lessons = data.get("lessons")
    if not isinstance(raw_lessons, list) or len(raw_lessons) != 12:
        raise ContentValidationError("lesson manifest must contain exactly 12 lessons")

    lessons: list[dict[str, Any]] = []
    ids: list[str] = []
    sequences: list[int] = []
    units: list[int] = []
    for index, raw_lesson in enumerate(raw_lessons):
        lesson = _require_object(raw_lesson, f"lesson manifest lessons[{index}]")
        for field in ("id", "title", "concept", "skill_objective"):
            _require_string(lesson.get(field), f"lesson manifest lessons[{index}].{field}")
        for field, maximum in (("unit", 4), ("sequence", 12)):
            value = lesson.get(field)
            if not _is_int(value) or not 1 <= value <= maximum:
                raise ContentValidationError(
                    f"lesson manifest lessons[{index}].{field} must be in range"
                )
        dimensions = lesson.get("dimensions")
        if not isinstance(dimensions, list) or not dimensions:
            raise ContentValidationError(f"lesson manifest lessons[{index}].dimensions must be non-empty")
        if any(not isinstance(dimension, str) for dimension in dimensions):
            raise ContentValidationError(f"lesson manifest lessons[{index}].dimensions must be strings")
        if len(dimensions) != len(set(dimensions)) or not set(dimensions) <= ALLOWED_DIMENSIONS:
            raise ContentValidationError(f"lesson manifest lessons[{index}].dimensions are invalid")
        ids.append(lesson["id"])
        sequences.append(lesson["sequence"])
        units.append(lesson["unit"])
        lessons.append(lesson)

    if len(ids) != len(set(ids)):
        raise ContentValidationError("lesson manifest lesson ids must be unique")
    if set(sequences) != set(range(1, 13)):
        raise ContentValidationError("lesson manifest sequences must uniquely cover 1 through 12")
    if set(units) != set(range(1, 5)):
        raise ContentValidationError("lesson manifest units must cover 1 through 4")

    raw_routing = _require_object(data.get("routing"), "lesson manifest routing")
    if set(raw_routing) != ALLOWED_DIMENSIONS:
        raise ContentValidationError("lesson manifest routing must contain the four allowed dimensions")
    routing: dict[str, tuple[str, ...]] = {}
    lesson_ids = set(ids)
    for dimension in ALLOWED_DIMENSIONS:
        row = raw_routing[dimension]
        if not isinstance(row, list) or not row or any(not isinstance(item, str) for item in row):
            raise ContentValidationError(f"lesson manifest routing.{dimension} must be a non-empty id list")
        if len(row) != len(set(row)) or not set(row) <= lesson_ids:
            raise ContentValidationError(f"lesson manifest routing.{dimension} contains invalid lesson ids")
        routing[dimension] = tuple(row)

    for lesson in lessons:
        routed_dimensions = {
            dimension for dimension, row in routing.items() if lesson["id"] in row
        }
        if set(lesson["dimensions"]) != routed_dimensions:
            raise ContentValidationError(
                f"lesson manifest dimensions for {lesson['id']} contradict routing"
            )
    return tuple(sorted(lessons, key=lambda lesson: lesson["sequence"])), routing


def _validate_lesson(lesson: Any, path: Path, metadata: dict[str, Any], routing: dict[str, tuple[str, ...]]) -> dict[str, Any]:
    data = _require_object(lesson, f"lesson file {path.name}")
    for field in ("schema_version", *METADATA_FIELDS, *CONTENT_BLOCKS):
        if field not in data:
            raise ContentValidationError(f"lesson file {path.name} is missing required field {field}")
    if data["schema_version"] != 1:
        raise ContentValidationError(f"lesson file {path.name} schema_version must be 1")
    if data["id"] != path.stem:
        raise ContentValidationError(f"lesson file {path.name} id must match its filename")
    for field in ("id", "title", "concept", "skill_objective"):
        _require_string(data[field], f"lesson file {path.name}.{field}")
    for field, maximum in (("unit", 4), ("sequence", 12)):
        if not _is_int(data[field]) or not 1 <= data[field] <= maximum:
            raise ContentValidationError(f"lesson file {path.name}.{field} must be in range")
    for field in ("id", "title", "unit", "sequence", "concept", "skill_objective"):
        if data[field] != metadata[field]:
            raise ContentValidationError(f"lesson file {path.name}.{field} does not match manifest metadata")

    dimensions = data["dimensions"]
    if not isinstance(dimensions, list) or not dimensions or any(not isinstance(item, str) for item in dimensions):
        raise ContentValidationError(f"lesson file {path.name}.dimensions must be a non-empty string array")
    if len(dimensions) != len(set(dimensions)) or not set(dimensions) <= ALLOWED_DIMENSIONS:
        raise ContentValidationError(f"lesson file {path.name}.dimensions are invalid")
    expected_dimensions = {dimension for dimension, row in routing.items() if data["id"] in row}
    if set(dimensions) != expected_dimensions:
        raise ContentValidationError(f"lesson file {path.name}.dimensions contradict manifest routing")

    concept_intro = _require_object(data["concept_intro"], f"lesson file {path.name}.concept_intro")
    _require_string(concept_intro.get("text"), f"lesson file {path.name}.concept_intro.text")

    example = _require_object(data["example"], f"lesson file {path.name}.example")
    _require_string(example.get("setting"), f"lesson file {path.name}.example.setting")
    has_dialogue = "dialogue" in example
    has_narration = "narration" in example
    if not has_dialogue and not has_narration:
        raise ContentValidationError(f"lesson file {path.name}.example needs dialogue or narration")
    if has_dialogue:
        dialogue = example["dialogue"]
        if not isinstance(dialogue, list) or not dialogue:
            raise ContentValidationError(f"lesson file {path.name}.example.dialogue must be a non-empty array")
        for index, item in enumerate(dialogue):
            line = _require_object(item, f"lesson file {path.name}.example.dialogue[{index}]")
            _require_string(line.get("speaker"), f"lesson file {path.name}.example.dialogue[{index}].speaker")
            _require_string(line.get("text"), f"lesson file {path.name}.example.dialogue[{index}].text")
    if has_narration:
        _require_string(example["narration"], f"lesson file {path.name}.example.narration")

    responses = _require_object(data["responses"], f"lesson file {path.name}.responses")
    if set(responses) != {"bad", "better", "best"}:
        raise ContentValidationError(f"lesson file {path.name}.responses must contain exactly bad, better, and best")
    for name in ("bad", "better", "best"):
        response = _require_object(responses[name], f"lesson file {path.name}.responses.{name}")
        _require_string(response.get("text"), f"lesson file {path.name}.responses.{name}.text")
        _require_string(response.get("explanation"), f"lesson file {path.name}.responses.{name}.explanation")

    exercise = _require_object(data["exercise"], f"lesson file {path.name}.exercise")
    _require_string(exercise.get("prompt"), f"lesson file {path.name}.exercise.prompt")
    exercise_options = _require_options(exercise.get("options"), f"lesson file {path.name}.exercise.options")
    _require_index(exercise.get("correct_option_index"), exercise_options, f"lesson file {path.name}.exercise.correct_option_index")

    practice = _require_object(data["practice"], f"lesson file {path.name}.practice")
    for field in ("type", "scenario_setup", "user_task"):
        _require_string(practice.get(field), f"lesson file {path.name}.practice.{field}")
    if practice["type"] != PRACTICE_TYPES[data["id"]]:
        raise ContentValidationError(f"lesson file {path.name}.practice.type does not match the locked path")

    completion_check = _require_object(data["completion_check"], f"lesson file {path.name}.completion_check")
    parts = completion_check.get("parts")
    if not isinstance(parts, list) or not parts:
        raise ContentValidationError(f"lesson file {path.name}.completion_check.parts must be non-empty")
    has_choice = False
    for index, raw_part in enumerate(parts):
        part = _require_object(raw_part, f"lesson file {path.name}.completion_check.parts[{index}]")
        kind = part.get("kind")
        if kind == "choice":
            has_choice = True
            _require_string(part.get("question"), f"lesson file {path.name}.completion_check.parts[{index}].question")
            options = _require_options(part.get("options"), f"lesson file {path.name}.completion_check.parts[{index}].options")
            _require_index(part.get("correct_option_index"), options, f"lesson file {path.name}.completion_check.parts[{index}].correct_option_index")
        elif kind == "free_draft":
            _require_string(part.get("prompt"), f"lesson file {path.name}.completion_check.parts[{index}].prompt")
            _require_string(part.get("good_answer_demonstrates"), f"lesson file {path.name}.completion_check.parts[{index}].good_answer_demonstrates")
            if part.get("grading") != "deferred-v1":
                raise ContentValidationError(f"lesson file {path.name}.completion_check.parts[{index}].grading must be deferred-v1")
        else:
            raise ContentValidationError(f"lesson file {path.name}.completion_check.parts[{index}].kind is invalid")
    if not has_choice:
        raise ContentValidationError(f"lesson file {path.name}.completion_check needs a choice part")
    return data


def load_curriculum(manifest_path: Path, lessons_dir: Path) -> Curriculum:
    """Load the manifest and every authored lesson, failing fast on invalid content."""
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ContentValidationError(f"could not load lesson manifest {manifest_path}: {error}") from error
    lessons, routing = _validate_manifest(manifest)
    metadata_by_id = {lesson["id"]: lesson for lesson in lessons}

    content: dict[str, dict[str, Any]] = {}
    try:
        paths = sorted(lessons_dir.glob("*.json"))
    except OSError as error:
        raise ContentValidationError(f"could not list lesson files in {lessons_dir}: {error}") from error
    for path in paths:
        try:
            raw_lesson = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ContentValidationError(f"could not load lesson file {path}: {error}") from error
        lesson_object = _require_object(raw_lesson, f"lesson file {path.name}")
        lesson_id = lesson_object.get("id")
        if not isinstance(lesson_id, str) or lesson_id not in metadata_by_id:
            raise ContentValidationError(f"lesson file {path.name} has an id not present in the manifest")
        content[lesson_id] = _validate_lesson(lesson_object, path, metadata_by_id[lesson_id], routing)
    return Curriculum(lessons=lessons, routing=routing, content=content)
