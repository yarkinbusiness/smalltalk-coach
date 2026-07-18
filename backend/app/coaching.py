"""Text coaching API. Screenshot requests intentionally return 501 until that cycle ships."""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Callable

from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse

from .diagnosis import (
    AnthropicDiagnosisAdapter,
    CoachingRefusedError,
    DiagnosisAdapter,
    DiagnosisError,
    diagnose,
)
from .routing import RoutingError, route_diagnosis
from .transcript import UnreadableTranscriptError, normalize_text


LOGGER = logging.getLogger(__name__)
router = APIRouter(prefix="/coaching", tags=["coaching"])


def _invalid_request() -> HTTPException:
    return HTTPException(status_code=400, detail="invalid_request")


def _require_user_id(user_id: object) -> str:
    if not isinstance(user_id, str) or not user_id.strip():
        raise _invalid_request()
    return user_id


def _adapter_for(request: Request) -> DiagnosisAdapter:
    return request.app.state.diagnosis_adapter


def _forbidden_terms(request: Request) -> set[str]:
    curriculum = request.app.state.curriculum
    return {str(lesson[field]) for lesson in curriculum.lessons for field in ("id", "title")}


def _report_response(row: dict[str, Any], request: Request) -> dict[str, Any]:
    curriculum = request.app.state.curriculum
    diagnosis = json.loads(row["diagnosis_json"])
    transcript = json.loads(row["transcript_json"])
    lesson = curriculum.lessons_by_id.get(row["lesson_id"])
    if lesson is None:
        LOGGER.error("coaching report missing_lesson report_id=%s", row["id"])
        raise HTTPException(status_code=502, detail="ai_unavailable")
    return {
        "id": row["id"],
        "status": "completed",
        "transcript": transcript,
        "diagnosis": diagnosis,
        "recommendation": {
            "weakest_dimension": row["weakest_dimension"],
            "selection_reason": "lowest_score",
            "lesson": {
                "id": lesson["id"], "title": lesson["title"], "concept": lesson["concept"],
                "skill_objective": lesson["skill_objective"],
                "recommendation_kind": row["recommendation_kind"],
            },
        },
        "practice_action": row["practice_action"],
    }


def _safety_guidance(category: str) -> str:
    if category in {"crisis", "self_harm"}:
        return "If you may be in immediate danger, contact local emergency services now. You can also reach a local crisis support service or a trusted person who can stay with you."
    if category == "abuse":
        return "If you are in immediate danger, contact local emergency services. Consider reaching a local abuse-support service or a trusted person who can help you make a safer plan."
    return "Please consider contacting local emergency, crisis, or abuse-support services, or a trusted person, for support that fits your situation."


@router.post("/diagnoses", status_code=201)
def create_diagnosis(body: dict[str, Any], request: Request) -> dict[str, Any]:
    user_id = _require_user_id(body.get("user_id"))
    if body.get("consent_to_process") is not True:
        raise HTTPException(status_code=400, detail="consent_required")
    source = body.get("source")
    if not isinstance(source, dict) or not isinstance(source.get("kind"), str):
        raise _invalid_request()
    if source["kind"] == "screenshot":
        raise HTTPException(status_code=501, detail="screenshot_not_implemented")
    if source["kind"] != "text" or set(source) != {"kind", "text"}:
        raise _invalid_request()
    try:
        transcript = normalize_text(source["text"])
    except (KeyError, UnreadableTranscriptError):
        raise HTTPException(status_code=422, detail="unreadable_transcript") from None
    try:
        diagnosis = diagnose(_adapter_for(request), transcript, _forbidden_terms(request))
    except CoachingRefusedError:
        raise HTTPException(status_code=422, detail="coaching_refused") from None
    except DiagnosisError:
        raise HTTPException(status_code=502, detail="ai_unavailable") from None
    safety = diagnosis["safety"]
    if safety["status"] == "escalate":
        return JSONResponse(status_code=200, content={
            "status": "safety_guidance",
            "category": safety["category"],
            "guidance": _safety_guidance(safety["category"]),
        })
    store = request.app.state.progress_store
    try:
        recommendation = route_diagnosis(
            diagnosis, request.app.state.curriculum, store.completed_lesson_ids(user_id)
        )
    except RoutingError:
        LOGGER.error("coaching routing configuration_error")
        raise HTTPException(status_code=502, detail="ai_unavailable") from None
    report_id = f"cr_{uuid.uuid4().hex}"
    created_at = store.save_coaching_report(
        report_id=report_id,
        user_id=user_id,
        transcript=transcript,
        diagnosis=diagnosis,
        weakest_dimension=recommendation["weakest_dimension"],
        lesson_id=recommendation["lesson"]["id"],
        recommendation_kind=recommendation["lesson"]["recommendation_kind"],
        practice_action=diagnosis["small_practice_action"],
    )
    row = {
        "id": report_id, "user_id": user_id, "created_at": created_at, "diagnosis_json": json.dumps(diagnosis),
        "transcript_json": json.dumps(transcript), "weakest_dimension": recommendation["weakest_dimension"],
        "lesson_id": recommendation["lesson"]["id"],
        "recommendation_kind": recommendation["lesson"]["recommendation_kind"],
        "practice_action": diagnosis["small_practice_action"],
    }
    return _report_response(row, request) | {"recommendation": recommendation}


@router.get("/reports/{report_id}")
def get_report(report_id: str, request: Request, user_id: str = Query(min_length=1)) -> dict[str, Any]:
    row = request.app.state.progress_store.coaching_report(report_id, _require_user_id(user_id))
    if row is None:
        raise HTTPException(status_code=404, detail="report_not_found")
    return _report_response(row, request)


@router.get("/reports")
def list_reports(request: Request, user_id: str = Query(min_length=1)) -> list[dict[str, str]]:
    return request.app.state.progress_store.coaching_report_summaries(_require_user_id(user_id))


@router.delete("/reports/{report_id}", status_code=204)
def delete_report(report_id: str, request: Request, user_id: str = Query(min_length=1)) -> Response:
    deleted = request.app.state.progress_store.delete_coaching_report(report_id, _require_user_id(user_id))
    if not deleted:
        raise HTTPException(status_code=404, detail="report_not_found")
    return Response(status_code=204)


def setup_coaching(app: Any, adapter_factory: Callable[[], DiagnosisAdapter] | None = None) -> None:
    """Install an injectable diagnosis adapter without constructing an SDK client."""
    app.state.diagnosis_adapter = (adapter_factory or AnthropicDiagnosisAdapter)()
    app.include_router(router)
