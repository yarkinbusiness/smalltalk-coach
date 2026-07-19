"""Structured vision extraction for screenshot coaching requests."""

from __future__ import annotations

import json
import logging
from typing import Any, Protocol

import anthropic

from .diagnosis import COACHING_MODEL, CoachingRefusedError
from .transcript import UnreadableTranscriptError


LOGGER = logging.getLogger(__name__)
_SPEAKERS = frozenset({"user", "other", "unknown"})
_SIDES = frozenset({"left", "right", "unknown"})

TRANSCRIPT_EXTRACTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_version", "source_kind", "user_speaker_id", "turns"],
    "properties": {
        "schema_version": {"const": 1},
        "source_kind": {"const": "screenshot"},
        "user_speaker_id": {"enum": ["user", None]},
        "turns": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["index", "speaker_id", "speaker", "text", "source"],
                "properties": {
                    "index": {"type": "integer"},
                    "speaker_id": {"type": "string", "minLength": 1},
                    "speaker": {"enum": sorted(_SPEAKERS)},
                    "text": {"type": "string", "minLength": 1},
                    "source": {"const": "vision"},
                },
            },
        },
        "unreadable_regions": {
            "type": "array", "items": {"type": "string", "minLength": 1},
        },
    },
}


class VisionError(RuntimeError):
    """A vision provider failure or response that cannot safely be used."""


class VisionAdapter(Protocol):
    def request(self, *, media_type: str, image_base64: str, user_message_side: str) -> Any: ...


class AnthropicVisionAdapter:
    """Create the SDK client lazily and make one bounded extraction call."""

    def __init__(self) -> None:
        self._client: anthropic.Anthropic | None = None

    def _client_for_request(self) -> anthropic.Anthropic:
        if self._client is None:
            self._client = anthropic.Anthropic()
        return self._client

    def request(self, *, media_type: str, image_base64: str, user_message_side: str) -> Any:
        instructions = (
            "Transcribe visible chat only into the requested transcript JSON. Preserve readable "
            "wording, punctuation, emoji, and message order. Mark unreadable regions with "
            "descriptions only; never reconstruct unreadable text. Use ONLY the caller-declared "
            f"user_message_side ({user_message_side!r}) to map bubbles to user or other; never "
            "use avatars, names, gender, or assumptions. Ignore app chrome, notifications, ads, "
            "and profile imagery. When only one side is visible or no side is declared, attribute "
            "messages to 'other' rather than guessing the user's side. Return JSON only; do not "
            "coach, summarize, or recommend."
        )
        return self._client_for_request().messages.create(
            model=COACHING_MODEL,
            max_tokens=4096,
            output_config={"format": {"type": "json_schema", "schema": TRANSCRIPT_EXTRACTION_SCHEMA}},
            messages=[{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_base64}},
                {"type": "text", "text": instructions},
            ]}],
        )


def _payload_from_response(response: Any) -> object:
    if isinstance(response, dict):
        if response.get("stop_reason") == "refusal":
            raise CoachingRefusedError()
        content = response.get("content")
        if isinstance(content, list) and content and isinstance(content[0], dict) and isinstance(content[0].get("text"), str):
            return json.loads(content[0]["text"])
        return response
    if getattr(response, "stop_reason", None) == "refusal":
        raise CoachingRefusedError()
    content = getattr(response, "content", None)
    if not isinstance(content, list) or not content:
        raise ValueError("missing content")
    text = getattr(content[0], "text", None)
    if text is None and isinstance(content[0], dict):
        text = content[0].get("text")
    if not isinstance(text, str):
        raise ValueError("missing json text")
    return json.loads(text)


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def validate_extraction(payload: object, user_message_side: object) -> dict[str, Any]:
    """Validate extraction fields and enforce the caller-only attribution rule."""
    if user_message_side not in _SIDES:
        raise UnreadableTranscriptError("invalid message side")
    if not isinstance(payload, dict):
        raise UnreadableTranscriptError("invalid extraction")
    expected = {"schema_version", "source_kind", "user_speaker_id", "turns"}
    if "unreadable_regions" in payload:
        expected.add("unreadable_regions")
    if set(payload) != expected or payload.get("schema_version") != 1 or payload.get("source_kind") != "screenshot":
        raise UnreadableTranscriptError("invalid extraction")
    regions = payload.get("unreadable_regions")
    if regions is not None and (not isinstance(regions, list) or any(not isinstance(region, str) or not region.strip() for region in regions)):
        raise UnreadableTranscriptError("invalid unreadable regions")
    turns = payload.get("turns")
    if not isinstance(turns, list) or not turns:
        raise UnreadableTranscriptError("no usable turns")
    normalized_turns: list[dict[str, Any]] = []
    for index, turn in enumerate(turns):
        if not isinstance(turn, dict) or set(turn) != {"index", "speaker_id", "speaker", "text", "source"}:
            raise UnreadableTranscriptError("invalid turn")
        if not _is_int(turn.get("index")) or turn["index"] < 0 or turn["index"] != index:
            raise UnreadableTranscriptError("non-contiguous turns")
        if turn.get("speaker") not in _SPEAKERS or turn.get("source") != "vision":
            raise UnreadableTranscriptError("invalid attribution")
        if not isinstance(turn.get("speaker_id"), str) or not turn["speaker_id"].strip() or not isinstance(turn.get("text"), str) or not turn["text"].strip():
            raise UnreadableTranscriptError("invalid turn text")
        normalized_turns.append({**turn, "speaker_id": turn["speaker_id"].strip(), "text": turn["text"].strip()})
    if user_message_side == "unknown":
        if payload.get("user_speaker_id") is not None or any(
            turn["speaker"] != "other" or turn["speaker_id"] != "other"
            for turn in normalized_turns
        ):
            raise UnreadableTranscriptError("guessed attribution")
    elif payload.get("user_speaker_id") != "user" or any(turn["speaker"] not in {"user", "other"} or turn["speaker_id"] != turn["speaker"] for turn in normalized_turns):
        raise UnreadableTranscriptError("invalid declared-side attribution")
    result = {"schema_version": 1, "source_kind": "screenshot", "user_speaker_id": payload["user_speaker_id"], "turns": normalized_turns}
    if regions is not None:
        result["unreadable_regions"] = [region.strip() for region in regions]
    return result


def extract_transcript(
    adapter: VisionAdapter, *, media_type: str, image_base64: str, user_message_side: str
) -> dict[str, Any]:
    """Make one extraction call and expose only safe failure categories."""
    try:
        response = adapter.request(
            media_type=media_type, image_base64=image_base64, user_message_side=user_message_side,
        )
        return validate_extraction(_payload_from_response(response), user_message_side)
    except CoachingRefusedError:
        raise
    except UnreadableTranscriptError:
        raise
    except (anthropic.APIConnectionError, anthropic.APITimeoutError, anthropic.APIStatusError) as error:
        LOGGER.error("coaching vision provider_error=%s", getattr(error, "status_code", "provider_error"))
        raise VisionError() from error
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
        LOGGER.error("coaching vision invalid_response")
        raise VisionError() from error
    except Exception as error:
        LOGGER.error("coaching vision provider_error=unknown")
        raise VisionError() from error
