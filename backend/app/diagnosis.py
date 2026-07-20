"""Structured Anthropic diagnosis adapter and strict response validation."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Protocol

import anthropic


LOGGER = logging.getLogger(__name__)
# Founder decision: "2026-07-19 — Coaching Models Locked to Haiku 4.5 Only (Founder Cost Constraint)".
COACHING_MODEL = "claude-haiku-4-5"
DIMENSIONS = ("warmth", "curiosity", "reciprocity", "flow")
_KINDS = frozenset({"observation", "inference", "suggestion"})
_SAFETY_CATEGORIES = frozenset({"crisis", "self_harm", "abuse", "other"})
_DEFAULT_DIAGNOSIS_ATTEMPTS = 3

DIAGNOSIS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schema_version", "mode", "incoming_interpretation", "response_coaching",
        "transferable_takeaway", "focus_dimension", "dimensions", "strengths",
        "improvements", "small_practice_action", "safety",
    ],
    "properties": {
        "schema_version": {"const": 1},
        "mode": {"enum": ["stimulus_only", "with_user_reply"]},
        "incoming_interpretation": {
            "type": "object",
            "additionalProperties": False,
            "required": ["tone", "intent", "response_goals"],
            "properties": {
                "tone": {"type": "string", "minLength": 1},
                "intent": {"type": "string", "minLength": 1},
                "response_goals": {"type": "string", "minLength": 1},
            },
        },
        "response_coaching": {
            "type": "object",
            "additionalProperties": False,
            "required": ["guidance", "example_responses"],
            "properties": {
                "guidance": {"type": "string", "minLength": 1},
                "example_responses": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 1},
                },
            },
        },
        "transferable_takeaway": {"type": "string", "minLength": 1},
        "focus_dimension": {"enum": list(DIMENSIONS)},
        "dimensions": {
            "anyOf": [
                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": list(DIMENSIONS),
                    "properties": {
                        dimension: {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["score", "observations"],
                            "properties": {
                                "score": {"enum": [1, 2, 3, 4, 5]},
                                "observations": {"type": "array", "items": {"$ref": "#/$defs/evidence"}},
                            },
                        }
                        for dimension in DIMENSIONS
                    },
                },
                {"type": "null"},
            ],
        },
        "strengths": {"type": "array", "items": {"$ref": "#/$defs/claim"}},
        "improvements": {"type": "array", "items": {"$ref": "#/$defs/improvement"}},
        "small_practice_action": {"type": "string", "minLength": 1},
        "safety": {
            "type": "object",
            "additionalProperties": False,
            "required": ["status", "category"],
            "properties": {"status": {"enum": ["clear", "escalate"]}, "category": {"enum": [None, "crisis", "self_harm", "abuse", "other"]}},
        },
    },
    "$defs": {
        "claim": {
            "type": "object", "additionalProperties": False,
            "required": ["text", "turn_indices", "quotes"],
            "properties": {"text": {"type": "string", "minLength": 1}, "turn_indices": {"type": "array", "items": {"type": "integer"}}, "quotes": {"type": "array", "items": {"type": "string", "minLength": 1}}},
        },
        "evidence": {
            "type": "object", "additionalProperties": False,
            "required": ["kind", "text", "turn_indices", "quotes"],
            "properties": {"kind": {"enum": sorted(_KINDS)}, "text": {"type": "string", "minLength": 1}, "turn_indices": {"type": "array", "items": {"type": "integer"}}, "quotes": {"type": "array", "items": {"type": "string", "minLength": 1}}},
        },
        "improvement": {
            "type": "object", "additionalProperties": False,
            "required": ["dimension", "priority", "kind", "text", "turn_indices", "quotes"],
            "properties": {"dimension": {"enum": list(DIMENSIONS)}, "priority": {"type": "integer"}, "kind": {"enum": sorted(_KINDS)}, "text": {"type": "string", "minLength": 1}, "turn_indices": {"type": "array", "items": {"type": "integer"}}, "quotes": {"type": "array", "items": {"type": "string", "minLength": 1}}},
        },
    },
}


class DiagnosisError(RuntimeError):
    """A provider failure or a response that cannot safely be used."""


class CoachingRefusedError(RuntimeError):
    """The provider declined the bounded coaching request."""


class DiagnosisAdapter(Protocol):
    def request(self, transcript: dict[str, Any]) -> Any: ...


class AnthropicDiagnosisAdapter:
    """Creates the Anthropic client only when a diagnosis is requested."""

    def __init__(self) -> None:
        self._client: anthropic.Anthropic | None = None

    def _client_for_request(self) -> anthropic.Anthropic:
        if self._client is None:
            self._client = anthropic.Anthropic()
        return self._client

    def request(self, transcript: dict[str, Any]) -> Any:
        return self._client_for_request().messages.create(
            model=COACHING_MODEL,
            max_tokens=8192,
            output_config={"format": {"type": "json_schema", "schema": DIAGNOSIS_SCHEMA}},
            messages=[{"role": "user", "content": json.dumps({"transcript": transcript}, ensure_ascii=False)}],
            system=(
                "You are a small-talk coach. Return only the requested diagnosis JSON. Turns whose "
                "speaker is 'user' belong to the person being coached; turns whose speaker is 'other' "
                "belong to the other party and are stimulus/context. NEVER score, praise, or critique "
                "the other party's words. If no user turns exist, return mode 'stimulus_only' with "
                "dimensions null: interpret the incoming message and coach how to construct a strong "
                "reply (structure, tone, what to include, and what to avoid), with one or two short "
                "example responses. If user turns exist, return mode 'with_user_reply' and score ONLY "
                "the user's turns. incoming_interpretation always addresses the most recent other-party "
                "message; when the transcript ends on a user turn, interpret the other-party message the "
                "user was responding to. When it ends on an other-party turn, response_coaching must "
                "address the user's next reply. Always provide a transferable_takeaway for similar future "
                "situations. Use only transcript evidence; do not select lessons. Return at most two "
                "improvements. Quotes must be verbatim substrings of transcript turns; use an empty quotes "
                "array for claims about missing behavior and never invent quotes. Escalate crisis, self-harm, "
                "or abuse instead of coaching."
            ),
        )


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _require_object(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("not an object")
    return value


def _require_string(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("not a non-empty string")
    return value


def _validate_evidence(
    value: object, turns: list[dict[str, Any]], *, needs_kind: bool,
    allowed_indices: set[int] | None = None,
) -> None:
    item = _require_object(value)
    expected = {"text", "turn_indices", "quotes"} | ({"kind"} if needs_kind else set())
    if set(item) != expected:
        raise ValueError("invalid evidence fields")
    _require_string(item["text"])
    if needs_kind and item["kind"] not in _KINDS:
        raise ValueError("invalid evidence kind")
    indexes, quotes = item["turn_indices"], item["quotes"]
    if not isinstance(indexes, list) or not indexes or any(not _is_int(index) or not 0 <= index < len(turns) for index in indexes):
        raise ValueError("invalid turn indices")
    if allowed_indices is not None and any(index not in allowed_indices for index in indexes):
        raise ValueError("evidence does not reference user turns")
    if not isinstance(quotes, list) or any(not isinstance(quote, str) or not quote for quote in quotes):
        raise ValueError("invalid quotes")
    referenced_text = [turns[index]["text"] for index in indexes]
    if any(not any(quote in text for text in referenced_text) for quote in quotes):
        raise ValueError("quote not present in referenced turn")


def _contains_forbidden_term(value: object, forbidden_terms: set[str]) -> bool:
    if isinstance(value, str):
        lowered = value.casefold()
        return any(term.casefold() in lowered for term in forbidden_terms)
    if isinstance(value, dict):
        return any(_contains_forbidden_term(item, forbidden_terms) for item in value.values())
    if isinstance(value, list):
        return any(_contains_forbidden_term(item, forbidden_terms) for item in value)
    return False


def _validate_interpretation(value: object) -> None:
    item = _require_object(value)
    if set(item) != {"tone", "intent", "response_goals"}:
        raise ValueError("invalid incoming interpretation")
    for field in item.values():
        _require_string(field)


def _validate_response_coaching(value: object) -> None:
    item = _require_object(value)
    if set(item) != {"guidance", "example_responses"}:
        raise ValueError("invalid response coaching")
    _require_string(item["guidance"])
    examples = item["example_responses"]
    if not isinstance(examples, list) or not 1 <= len(examples) <= 2:
        raise ValueError("invalid example responses")
    for example in examples:
        _require_string(example)


def validate_diagnosis(payload: object, transcript: dict[str, Any], forbidden_terms: set[str]) -> dict[str, Any]:
    """Validate contract rules JSON Schema cannot express against transcript turns."""
    diagnosis = _require_object(payload)
    expected = {
        "schema_version", "mode", "incoming_interpretation", "response_coaching",
        "transferable_takeaway", "focus_dimension", "dimensions", "strengths",
        "improvements", "small_practice_action", "safety",
    }
    if set(diagnosis) != expected or diagnosis["schema_version"] != 1:
        raise ValueError("invalid diagnosis fields")
    turns = transcript["turns"]
    user_indices = {index for index, turn in enumerate(turns) if turn.get("speaker") == "user"}
    expected_mode = "with_user_reply" if user_indices else "stimulus_only"
    if diagnosis["mode"] != expected_mode:
        raise ValueError("mode does not match transcript")
    _validate_interpretation(diagnosis["incoming_interpretation"])
    _validate_response_coaching(diagnosis["response_coaching"])
    _require_string(diagnosis["transferable_takeaway"])
    if diagnosis["focus_dimension"] not in DIMENSIONS:
        raise ValueError("invalid focus dimension")
    dimensions = diagnosis["dimensions"]
    if expected_mode == "stimulus_only":
        if dimensions is not None:
            raise ValueError("stimulus-only diagnosis must not score dimensions")
    else:
        dimensions = _require_object(dimensions)
        if set(dimensions) != set(DIMENSIONS):
            raise ValueError("invalid dimensions")
        for dimension in DIMENSIONS:
            item = _require_object(dimensions[dimension])
            if set(item) != {"score", "observations"} or item["score"] not in {1, 2, 3, 4, 5} or not _is_int(item["score"]):
                raise ValueError("invalid dimension score")
            if not isinstance(item["observations"], list):
                raise ValueError("invalid observations")
            for observation in item["observations"]:
                _validate_evidence(observation, turns, needs_kind=True, allowed_indices=user_indices)
        weakest_dimension = min(DIMENSIONS, key=lambda name: dimensions[name]["score"])
        if diagnosis["focus_dimension"] != weakest_dimension:
            raise ValueError("focus dimension does not match weakest score")
    strengths = diagnosis["strengths"]
    if not isinstance(strengths, list) or len(strengths) > 5:
        raise ValueError("invalid strengths")
    for strength in strengths:
        _validate_evidence(
            strength, turns, needs_kind=False,
            allowed_indices=user_indices if expected_mode == "with_user_reply" else None,
        )
    improvements = diagnosis["improvements"]
    minimum_improvements = 0 if expected_mode == "stimulus_only" else 1
    if not isinstance(improvements, list) or not minimum_improvements <= len(improvements) <= 4:
        raise ValueError("invalid improvements")
    priorities: set[int] = set()
    for improvement in improvements:
        item = _require_object(improvement)
        if set(item) != {"dimension", "priority", "kind", "text", "turn_indices", "quotes"}:
            raise ValueError("invalid improvement fields")
        if item["dimension"] not in DIMENSIONS or not _is_int(item["priority"]) or item["priority"] < 1:
            raise ValueError("invalid improvement")
        priorities.add(item["priority"])
        _validate_evidence(
            {key: item[key] for key in ("kind", "text", "turn_indices", "quotes")},
            turns, needs_kind=True,
            allowed_indices=user_indices if expected_mode == "with_user_reply" else None,
        )
    if len(priorities) != len(improvements):
        raise ValueError("duplicate priorities")
    _require_string(diagnosis["small_practice_action"])
    safety = _require_object(diagnosis["safety"])
    if set(safety) != {"status", "category"} or safety["status"] not in {"clear", "escalate"}:
        raise ValueError("invalid safety")
    if (safety["status"] == "clear" and safety["category"] is not None) or (safety["status"] == "escalate" and safety["category"] not in _SAFETY_CATEGORIES):
        raise ValueError("invalid safety category")
    if _contains_forbidden_term(diagnosis, forbidden_terms):
        raise ValueError("contains forbidden lesson reference")
    kept_improvements = sorted(improvements, key=lambda item: item["priority"])[:2]
    coerced_improvements = [
        {**improvement, "priority": priority}
        for priority, improvement in enumerate(kept_improvements, start=1)
    ]
    return {
        **diagnosis,
        "strengths": strengths[:3],
        "improvements": coerced_improvements,
    }


def _payload_from_response(response: Any) -> object:
    if isinstance(response, dict):
        if response.get("stop_reason") == "refusal":
            raise CoachingRefusedError()
        if "content" in response:
            content = response["content"]
            if isinstance(content, list) and content and isinstance(content[0], dict) and isinstance(content[0].get("text"), str):
                return json.loads(content[0]["text"])
        return response
    stop_reason = getattr(response, "stop_reason", None)
    if stop_reason == "refusal":
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


def _diagnosis_attempts() -> int:
    """Return the bounded per-request retry count without import-time config."""
    try:
        attempts = int(os.environ.get("SMALLTALK_DIAGNOSIS_ATTEMPTS", _DEFAULT_DIAGNOSIS_ATTEMPTS))
    except (TypeError, ValueError):
        return _DEFAULT_DIAGNOSIS_ATTEMPTS
    return attempts if 1 <= attempts <= 5 else _DEFAULT_DIAGNOSIS_ATTEMPTS


def _invalid_response_reason(error: Exception) -> str:
    if isinstance(error, json.JSONDecodeError):
        return error.msg
    if isinstance(error, ValueError):
        return str(error)
    return type(error).__name__


def diagnose(
    adapter: DiagnosisAdapter, transcript: dict[str, Any], forbidden_terms: set[str]
) -> dict[str, Any]:
    """Make a bounded diagnosis request and expose only safe errors."""
    attempts = _diagnosis_attempts()
    for attempt in range(1, attempts + 1):
        try:
            response = adapter.request(transcript)
            return validate_diagnosis(_payload_from_response(response), transcript, forbidden_terms)
        except CoachingRefusedError:
            raise
        except anthropic.APIStatusError as error:
            status = error.status_code
            if status < 500 and status != 429:
                LOGGER.error("coaching diagnosis provider_error=%s", status)
                raise DiagnosisError() from error
            LOGGER.error("coaching diagnosis attempt=%d/%d provider_error=%s", attempt, attempts, status)
            if attempt == attempts:
                LOGGER.error("coaching diagnosis exhausted attempts=%d", attempts)
                raise DiagnosisError() from error
        except (anthropic.APIConnectionError, anthropic.APITimeoutError) as error:
            LOGGER.error(
                "coaching diagnosis attempt=%d/%d provider_error=%s",
                attempt, attempts, type(error).__name__,
            )
            if attempt == attempts:
                LOGGER.error("coaching diagnosis exhausted attempts=%d", attempts)
                raise DiagnosisError() from error
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
            LOGGER.error(
                "coaching diagnosis attempt=%d/%d invalid_response reason=%s",
                attempt, attempts, _invalid_response_reason(error),
            )
            if attempt == attempts:
                LOGGER.error("coaching diagnosis exhausted attempts=%d", attempts)
                raise DiagnosisError() from error
    raise DiagnosisError()
