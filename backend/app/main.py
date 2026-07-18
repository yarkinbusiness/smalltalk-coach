"""FastAPI application for serving the locked v1 curriculum."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator, Annotated

from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel

from .content import Curriculum, load_curriculum
from .store import ProgressStore


class CompletionRequest(BaseModel):
    user_id: str
    answers: dict[str, object]


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


def create_app(
    *, manifest_path: Path | None = None, lessons_dir: Path | None = None, database_path: Path | None = None
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

    def curriculum_for(request: Request) -> Curriculum:
        return request.app.state.curriculum

    def progress_store_for(request: Request) -> ProgressStore:
        return request.app.state.progress_store

    @app.get("/health")
    def health(request: Request) -> dict[str, object]:
        curriculum = curriculum_for(request)
        return {"status": "ok", "lessons_loaded": len(curriculum.content)}

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

        feedback: dict[str, str] = {}
        parts = curriculum.content[lesson_id]["completion_check"]["parts"]
        for part_index, part in enumerate(parts):
            if part["kind"] != "choice":
                continue
            answer = body.answers.get(str(part_index))
            options = part["options"]
            if not isinstance(answer, int) or isinstance(answer, bool) or not 0 <= answer < len(options):
                feedback[str(part_index)] = "Choose one of the available options for this part."
            elif answer != part["correct_option_index"]:
                feedback[str(part_index)] = options[answer]["feedback"]
        if feedback:
            return {"completed": False, "feedback": feedback}

        store.record_completion(user_id, lesson_id)
        updated_completed = store.completed_lesson_ids(user_id)
        return {
            "completed": True,
            "unlocked_next": _unlocked_lesson_id(curriculum, updated_completed),
        }

    return app


app = create_app()
