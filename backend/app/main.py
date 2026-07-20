"""FastAPI application for serving the locked v1 curriculum."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime
import os
from pathlib import Path
from typing import Any, AsyncIterator, Annotated
import uuid
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel

from .content import Curriculum, load_curriculum
from .coaching import setup_coaching
from .diagnosis import DiagnosisAdapter
from .profile import build_profile
from .review import build_review_queue
from .streak import compute_streak, parse_activity_timestamp
from .store import ProgressStore


class CompletionRequest(BaseModel):
    user_id: str
    answers: dict[str, object]


class ReflectionRequest(BaseModel):
    subject_kind: str
    subject_id: str
    outcome: str
    note: object = ""


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _require_user_id(user_id: str) -> str:
    if not user_id.strip():
        raise HTTPException(status_code=422, detail="user_id must be non-empty")
    return user_id


def _unlocked_lesson_id(curriculum: Curriculum, completed: set[str]) -> str | None:
    return next(
        (lesson["id"] for lesson in curriculum.lessons if lesson["id"] not in completed),
        None,
    )


def _lesson_state(lesson_id: str, completed: set[str], unlocked_id: str | None) -> str:
    if lesson_id in completed:
        return "completed"
    if lesson_id == unlocked_id:
        return "unlocked"
    return "locked"


def _grade_completion(lesson: dict[str, Any], answers: dict[str, object]) -> dict[str, str]:
    """Apply the deterministic choice checks shared by lessons and reviews."""
    feedback: dict[str, str] = {}
    parts = lesson["completion_check"]["parts"]
    for part_index, part in enumerate(parts):
        if part["kind"] != "choice":
            continue
        answer = answers.get(str(part_index))
        options = part["options"]
        if not isinstance(answer, int) or isinstance(answer, bool) or not 0 <= answer < len(options):
            feedback[str(part_index)] = "Choose one of the available options for this part."
        elif answer != part["correct_option_index"]:
            feedback[str(part_index)] = options[answer]["feedback"]
    return feedback


def _timezone_or_422(tz: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise HTTPException(status_code=422, detail="invalid_timezone") from error


def _profile_for(store: ProgressStore, user_id: str, curriculum: Curriculum) -> dict[str, object]:
    return build_profile(
        store.coaching_report_rows(user_id),
        store.completed_lesson_ids(user_id),
        curriculum,
        store.reflections(user_id),
    )


def _review_priority_dimension(profile: dict[str, object]) -> str | None:
    """Use a recurring weakness, otherwise the highest all-time flagged dimension."""
    recurring = profile.get("recurring_weakness")
    if isinstance(recurring, dict) and isinstance(recurring.get("dimension"), str):
        return recurring["dimension"]

    dimensions = profile.get("dimensions")
    if not isinstance(dimensions, dict):
        return None
    priority: str | None = None
    highest_count = 0
    for dimension, value in dimensions.items():
        if not isinstance(value, dict):
            continue
        flagged_count = value.get("flagged_count")
        if isinstance(flagged_count, int) and flagged_count > highest_count:
            priority = dimension
            highest_count = flagged_count
    return priority


def _review_queue_for(
    store: ProgressStore,
    user_id: str,
    curriculum: Curriculum,
    timezone: ZoneInfo,
    now: datetime,
) -> list[dict[str, str | int]]:
    timestamps = store.activity_timestamps(user_id)
    lesson_completions = [
        (lesson_id, parsed)
        for lesson_id, raw_timestamp in timestamps["lesson_completions"]
        if (parsed := parse_activity_timestamp(raw_timestamp)) is not None
    ]
    review_completions = [
        (lesson_id, parsed)
        for lesson_id, raw_timestamp in timestamps["review_completions"]
        if (parsed := parse_activity_timestamp(raw_timestamp)) is not None
    ]
    profile = _profile_for(store, user_id, curriculum)
    return build_review_queue(
        lesson_completions,
        review_completions,
        curriculum,
        _review_priority_dimension(profile),
        timezone,
        now,
    )


def create_app(
    *, manifest_path: Path | None = None, lessons_dir: Path | None = None,
    database_path: Path | None = None, diagnosis_adapter: DiagnosisAdapter | None = None,
) -> FastAPI:
    """Create an app whose curriculum is loaded and validated at startup."""
    repo_root = _default_repo_root()
    selected_manifest = manifest_path or repo_root / "content" / "lesson_path.json"
    selected_lessons_dir = lessons_dir or repo_root / "content" / "lessons"
    selected_database = database_path or repo_root / "backend" / "data" / "progress.db"

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.curriculum = load_curriculum(selected_manifest, selected_lessons_dir)
        app.state.progress_store = ProgressStore(selected_database)
        yield

    app = FastAPI(title="Smalltalk Coach", lifespan=lifespan)
    setup_coaching(app, (lambda: diagnosis_adapter) if diagnosis_adapter is not None else None)

    def curriculum_for(request: Request) -> Curriculum:
        return request.app.state.curriculum

    def progress_store_for(request: Request) -> ProgressStore:
        return request.app.state.progress_store

    @app.get("/health")
    def health(request: Request) -> dict[str, object]:
        curriculum = curriculum_for(request)
        return {
            "status": "ok",
            "lessons_loaded": len(curriculum.content),
            "coaching_enabled": "ANTHROPIC_API_KEY" in os.environ,
        }

    @app.get("/curriculum")
    def get_curriculum(
        request: Request,
        user_id: Annotated[str, Query(min_length=1)],
    ) -> dict[str, object]:
        user_id = _require_user_id(user_id)
        curriculum = curriculum_for(request)
        completed = progress_store_for(request).completed_lesson_ids(user_id)
        unlocked_id = _unlocked_lesson_id(curriculum, completed)
        units: list[dict[str, object]] = []
        for unit in range(1, 5):
            unit_lessons: list[dict[str, object]] = []
            for lesson in curriculum.lessons:
                if lesson["unit"] != unit:
                    continue
                item = dict(lesson)
                item["content_available"] = lesson["id"] in curriculum.content
                item["state"] = _lesson_state(lesson["id"], completed, unlocked_id)
                unit_lessons.append(item)
            units.append({"unit": unit, "lessons": unit_lessons})
        return {"units": units}

    @app.get("/users/{user_id}/streak")
    def get_streak(
        user_id: str,
        request: Request,
        tz: str = "UTC",
    ) -> dict[str, object]:
        user_id = _require_user_id(user_id)
        timezone = _timezone_or_422(tz)

        curriculum = curriculum_for(request)
        store = progress_store_for(request)
        timestamps = store.activity_timestamps(user_id)
        lesson_completions = [
            (lesson_id, parsed)
            for lesson_id, raw_timestamp in timestamps["lesson_completions"]
            if (parsed := parse_activity_timestamp(raw_timestamp)) is not None
        ]
        coaching_reports = [
            parsed
            for raw_timestamp in timestamps["coaching_reports"]
            if (parsed := parse_activity_timestamp(raw_timestamp)) is not None
        ]
        review_completions = [
            parsed
            for _, raw_timestamp in timestamps["review_completions"]
            if (parsed := parse_activity_timestamp(raw_timestamp)) is not None
        ]
        unit_lessons: dict[int, list[str]] = {}
        for lesson in curriculum.lessons:
            unit_lessons.setdefault(lesson["unit"], []).append(lesson["id"])
        now = datetime.now(UTC)
        streak = compute_streak(
            lesson_completions,
            coaching_reports,
            unit_lessons,
            timezone,
            now,
            review_completions=review_completions,
        )

        completed = store.completed_lesson_ids(user_id)
        unlocked_id = _unlocked_lesson_id(curriculum, completed)
        if unlocked_id is None:
            due = _review_queue_for(store, user_id, curriculum, timezone, now)
            if due:
                head = due[0]
                today: dict[str, str | None] = {
                    "kind": "review",
                    "lesson_id": str(head["lesson_id"]),
                    "title": str(head["title"]),
                    "unit_id": str(head["unit_id"]),
                }
            else:
                today = {
                    "kind": "all_complete", "lesson_id": None, "title": None, "unit_id": None,
                }
        else:
            lesson = curriculum.lessons_by_id[unlocked_id]
            today = {
                "kind": "lesson",
                "lesson_id": lesson["id"],
                "title": lesson["title"],
                "unit_id": f"u{lesson['unit']}",
            }
        return {
            "streak_days": streak["streak_days"],
            "active_today": streak["active_today"],
            "freezes": streak["freezes"],
            "today": today,
        }

    @app.get("/users/{user_id}/review-queue")
    def get_review_queue(
        user_id: str,
        request: Request,
        tz: str = "UTC",
    ) -> dict[str, object]:
        user_id = _require_user_id(user_id)
        timezone = _timezone_or_422(tz)
        return {
            "due": _review_queue_for(
                progress_store_for(request),
                user_id,
                curriculum_for(request),
                timezone,
                datetime.now(UTC),
            )
        }

    @app.get("/users/{user_id}/profile")
    def get_profile(user_id: str, request: Request) -> dict[str, object]:
        user_id = _require_user_id(user_id)
        store = progress_store_for(request)
        return _profile_for(store, user_id, curriculum_for(request))

    @app.post("/users/{user_id}/reflections", status_code=201)
    def create_reflection(
        user_id: str,
        body: ReflectionRequest,
        request: Request,
    ) -> dict[str, str]:
        user_id = _require_user_id(user_id)
        if body.subject_kind not in {"lesson", "report"}:
            raise HTTPException(status_code=422, detail="invalid_subject_kind")
        if body.outcome not in {"went_well", "partly", "avoided"}:
            raise HTTPException(status_code=422, detail="invalid_outcome")
        if not isinstance(body.note, str) or len(body.note) > 500:
            raise HTTPException(status_code=422, detail="invalid_note")

        store = progress_store_for(request)
        if body.subject_kind == "lesson":
            subject_exists = body.subject_id in curriculum_for(request).lessons_by_id
        else:
            subject_exists = store.coaching_report(body.subject_id, user_id) is not None
        if not subject_exists:
            raise HTTPException(status_code=404, detail="unknown_subject")

        reflection_id = str(uuid.uuid4())
        created_at = store.save_reflection(
            reflection_id=reflection_id,
            user_id=user_id,
            subject_kind=body.subject_kind,
            subject_id=body.subject_id,
            outcome=body.outcome,
            note=body.note,
        )
        return {"id": reflection_id, "created_at": created_at}

    @app.get("/users/{user_id}/reflections")
    def get_reflections(user_id: str, request: Request) -> dict[str, object]:
        user_id = _require_user_id(user_id)
        return {"reflections": progress_store_for(request).reflections(user_id)}

    @app.get("/lessons/{lesson_id}")
    def get_lesson(
        lesson_id: str,
        request: Request,
        user_id: Annotated[str, Query(min_length=1)],
    ) -> dict[str, Any]:
        user_id = _require_user_id(user_id)
        curriculum = curriculum_for(request)
        if lesson_id not in curriculum.lessons_by_id:
            raise HTTPException(status_code=404, detail="lesson_not_found")
        completed = progress_store_for(request).completed_lesson_ids(user_id)
        unlocked_id = _unlocked_lesson_id(curriculum, completed)
        if _lesson_state(lesson_id, completed, unlocked_id) == "locked":
            raise HTTPException(status_code=423, detail="locked")
        if lesson_id not in curriculum.content:
            raise HTTPException(status_code=404, detail="content_pending")
        return curriculum.content[lesson_id]

    @app.post("/lessons/{lesson_id}/complete")
    def complete_lesson(
        lesson_id: str,
        body: CompletionRequest,
        request: Request,
    ) -> dict[str, object]:
        user_id = _require_user_id(body.user_id)
        curriculum = curriculum_for(request)
        if lesson_id not in curriculum.lessons_by_id:
            raise HTTPException(status_code=404, detail="lesson_not_found")
        store = progress_store_for(request)
        completed = store.completed_lesson_ids(user_id)
        unlocked_id = _unlocked_lesson_id(curriculum, completed)
        if _lesson_state(lesson_id, completed, unlocked_id) == "locked":
            raise HTTPException(status_code=423, detail="locked")
        if lesson_id not in curriculum.content:
            raise HTTPException(status_code=404, detail="content_pending")

        feedback = _grade_completion(curriculum.content[lesson_id], body.answers)
        if feedback:
            return {"completed": False, "feedback": feedback}

        store.record_completion(user_id, lesson_id)
        updated_completed = store.completed_lesson_ids(user_id)
        return {
            "completed": True,
            "unlocked_next": _unlocked_lesson_id(curriculum, updated_completed),
        }

    @app.post("/lessons/{lesson_id}/review")
    def review_lesson(
        lesson_id: str,
        body: CompletionRequest,
        request: Request,
    ) -> dict[str, object]:
        user_id = _require_user_id(body.user_id)
        curriculum = curriculum_for(request)
        if lesson_id not in curriculum.lessons_by_id:
            raise HTTPException(status_code=404, detail="lesson_not_found")
        store = progress_store_for(request)
        completed = store.completed_lesson_ids(user_id)
        if lesson_id not in completed:
            raise HTTPException(status_code=409, detail="not_completed")
        if lesson_id not in curriculum.content:
            raise HTTPException(status_code=404, detail="content_pending")

        feedback = _grade_completion(curriculum.content[lesson_id], body.answers)
        if feedback:
            return {"completed": False, "feedback": feedback}

        store.record_review(user_id, lesson_id)
        return {
            "completed": True,
            "unlocked_next": _unlocked_lesson_id(curriculum, completed),
        }

    return app


app = create_app()
