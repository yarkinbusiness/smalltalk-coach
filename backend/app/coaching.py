"""Coaching API for synchronous text and asynchronous screenshot requests."""

from __future__ import annotations

import base64
import binascii
import json
import logging
import uuid
from typing import Any, Callable

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, Response
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
from .jobs import CoachingJobStore
from .vision import AnthropicVisionAdapter, VisionError, extract_transcript


LOGGER = logging.getLogger(__name__)
router = APIRouter(prefix="/coaching", tags=["coaching"])
_IMAGE_MEDIA_TYPES = frozenset({"image/png", "image/jpeg", "image/webp"})
_MAX_IMAGE_BYTES = 10 * 1024 * 1024


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
            "selection_reason": "focus_dimension" if diagnosis["dimensions"] is None else "lowest_score",
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


def _validate_image(source: dict[str, Any]) -> tuple[str, str, str]:
    expected = {"kind", "media_type", "image_base64", "user_message_side"}
    if not set(source).issubset(expected) or not {"kind", "media_type", "image_base64"}.issubset(source):
        raise _invalid_request()
    media_type, encoded = source["media_type"], source["image_base64"]
    side = source.get("user_message_side", "unknown")
    if not isinstance(media_type, str) or media_type not in _IMAGE_MEDIA_TYPES:
        raise HTTPException(status_code=415, detail="unsupported_image_type")
    if not isinstance(encoded, str) or not isinstance(side, str) or side not in {"left", "right", "unknown"}:
        raise _invalid_request()
    try:
        image_bytes = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=422, detail="bad_image") from None
    try:
        if len(image_bytes) > _MAX_IMAGE_BYTES:
            raise HTTPException(status_code=413, detail="image_too_large")
        valid_magic = (
            (media_type == "image/png" and image_bytes.startswith(b"\x89PNG"))
            or (media_type == "image/jpeg" and image_bytes.startswith(b"\xff\xd8\xff"))
            or (media_type == "image/webp" and len(image_bytes) >= 12 and image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP")
        )
        if not valid_magic:
            raise HTTPException(status_code=422, detail="bad_image")
    finally:
        del image_bytes
    return media_type, encoded, side


def _persist_diagnosis(request: Request, user_id: str, transcript: dict[str, Any], diagnosis: dict[str, Any]) -> str:
    store = request.app.state.progress_store
    try:
        recommendation = route_diagnosis(diagnosis, request.app.state.curriculum, store.completed_lesson_ids(user_id))
    except RoutingError:
        LOGGER.error("coaching routing configuration_error")
        raise DiagnosisError() from None
    report_id = f"cr_{uuid.uuid4().hex}"
    store.save_coaching_report(
        report_id=report_id, user_id=user_id, transcript=transcript, diagnosis=diagnosis,
        weakest_dimension=recommendation["weakest_dimension"], lesson_id=recommendation["lesson"]["id"],
        recommendation_kind=recommendation["lesson"]["recommendation_kind"],
        practice_action=diagnosis["small_practice_action"],
    )
    return report_id


def _run_screenshot_job(
    app: Any, job_id: str, user_id: str, media_type: str, image_base64: str, user_message_side: str,
) -> None:
    """Run the bounded screenshot pipeline; decoded image bytes never leave this function."""
    jobs: CoachingJobStore = app.state.coaching_jobs
    image_bytes: bytes | None = None
    try:
        image_bytes = base64.b64decode(image_base64, validate=True)
        transcript = extract_transcript(
            app.state.vision_adapter, media_type=media_type, image_base64=image_base64,
            user_message_side=user_message_side,
        )
        del image_base64
        diagnosis = diagnose(app.state.diagnosis_adapter, transcript, {
            str(lesson[field]) for lesson in app.state.curriculum.lessons for field in ("id", "title")
        })
        safety = diagnosis["safety"]
        if safety["status"] == "escalate":
            jobs.complete_safety(job_id, safety["category"], _safety_guidance(safety["category"]))
            return
        report_id = _persist_diagnosis(_AppRequest(app), user_id, transcript, diagnosis)
        jobs.complete_report(job_id, report_id)
    except CoachingRefusedError:
        jobs.fail(job_id, status_code=422, detail="coaching_refused")
    except UnreadableTranscriptError:
        jobs.fail(job_id, status_code=422, detail="unreadable_transcript")
    except (VisionError, DiagnosisError):
        jobs.fail(job_id, status_code=502, detail="ai_unavailable")
    except (ValueError, TypeError, KeyError, binascii.Error):
        jobs.fail(job_id, status_code=502, detail="ai_unavailable")
    except Exception:
        jobs.fail(job_id, status_code=502, detail="ai_unavailable")
    finally:
        if image_bytes is not None:
            del image_bytes
        # If extraction raised before its normal disposal point, drop the encoded payload too.
        try:
            del image_base64
        except UnboundLocalError:
            pass


class _AppRequest:
    """Minimal request facade for helpers shared by request and background paths."""

    def __init__(self, app: Any) -> None:
        self.app = app


@router.post("/diagnoses", status_code=201)
def create_diagnosis(body: dict[str, Any], request: Request, background_tasks: BackgroundTasks) -> dict[str, Any]:
    user_id = _require_user_id(body.get("user_id"))
    if body.get("consent_to_process") is not True:
        raise HTTPException(status_code=400, detail="consent_required")
    source = body.get("source")
    if not isinstance(source, dict) or not isinstance(source.get("kind"), str):
        raise _invalid_request()
    if source["kind"] == "screenshot":
        media_type, image_base64, user_message_side = _validate_image(source)
        job = request.app.state.coaching_jobs.create(user_id)
        background_tasks.add_task(
            _run_screenshot_job, request.app, job["id"], user_id, media_type, image_base64, user_message_side,
        )
        return JSONResponse(status_code=202, content={
            "job_id": job["id"], "status": "processing",
            "poll_url": f"/coaching/diagnoses/jobs/{job['id']}",
        })
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
    try:
        report_id = _persist_diagnosis(request, user_id, transcript, diagnosis)
    except DiagnosisError:
        raise HTTPException(status_code=502, detail="ai_unavailable") from None
    row = request.app.state.progress_store.coaching_report(report_id, user_id)
    if row is None:
        raise HTTPException(status_code=502, detail="ai_unavailable")
    return _report_response(row, request)


@router.get("/diagnoses/jobs/{job_id}")
def get_diagnosis_job(job_id: str, request: Request, user_id: str = Query(min_length=1)) -> dict[str, Any]:
    job = request.app.state.coaching_jobs.get(job_id, _require_user_id(user_id))
    if job is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    if job["status"] == "processing":
        return {"status": "processing"}
    if job["status"] == "failed":
        return {"status": "failed", "detail": job["detail"]}
    if job["status"] == "safety_guidance":
        return {"status": "safety_guidance", "category": job["category"], "guidance": job["guidance"]}
    row = request.app.state.progress_store.coaching_report(job["report_id"], user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    return _report_response(row, request)


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
    """Install injectable adapters and the ephemeral screenshot job store."""
    app.state.diagnosis_adapter = (adapter_factory or AnthropicDiagnosisAdapter)()
    app.state.vision_adapter = AnthropicVisionAdapter()
    app.state.coaching_jobs = CoachingJobStore()
    app.include_router(router)
