"""Structured Anthropic adapter for optional free-draft feedback."""

from __future__ import annotations

from datetime import UTC, datetime
import json
import logging
import math
import os
from threading import Lock
from typing import Any, Protocol

import anthropic

from .diagnosis import COACHING_MODEL


LOGGER = logging.getLogger(__name__)
_DEFAULT_MONTHLY_BUDGET_USD = 5.00
_DEFAULT_GRADING_ATTEMPTS = 3
# Haiku 4.5 pricing verified live on 2026-07-21.
_INPUT_COST_PER_TOKEN_USD = 1.00 / 1_000_000
_OUTPUT_COST_PER_TOKEN_USD = 5.00 / 1_000_000

GRADING_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["met_criteria", "feedback"],
    "properties": {
        "met_criteria": {"type": "boolean"},
        "feedback": {"type": "string", "minLength": 1},
    },
}


class DraftGradingError(RuntimeError):
    """A provider failure or a response that cannot safely be used."""


class DraftGradingRefusedError(RuntimeError):
    """The provider declined the bounded draft-grading request."""


class BudgetExceededError(RuntimeError):
    """The in-memory UTC calendar-month draft-grading ceiling was reached."""


class DraftGradingAdapter(Protocol):
    def request(self, prompt: str, good_answer_demonstrates: str, draft: str) -> Any: ...


class AnthropicDraftGradingAdapter:
    """Creates the Anthropic client only when a draft is submitted."""

    def __init__(self) -> None:
        self._client: anthropic.Anthropic | None = None

    def _client_for_request(self) -> anthropic.Anthropic:
        if self._client is None:
            self._client = anthropic.Anthropic()
        return self._client

    def request(self, prompt: str, good_answer_demonstrates: str, draft: str) -> Any:
        return self._client_for_request().messages.create(
            model=COACHING_MODEL,
            max_tokens=1024,
            output_config={"format": {"type": "json_schema", "schema": GRADING_SCHEMA}},
            messages=[{"role": "user", "content": json.dumps({
                "prompt": prompt,
                "good_answer_demonstrates": good_answer_demonstrates,
                "draft": draft,
            }, ensure_ascii=False)}],
            system=(
                "You are a small-talk coach giving feedback on a short written practice exercise. "
                "You are given the prompt shown to the user, a description of what a good answer "
                "demonstrates, and the user's draft. Decide whether the draft demonstrates what is "
                "described. Give brief, specific, encouraging feedback in 2-4 sentences, referencing "
                "concrete wording from the draft where useful. Never invent claims about what the draft "
                "says or grade against criteria not provided. Return only the requested JSON."
            ),
        )


class DraftGradingBudget:
    """Thread-safe UTC calendar-month spend tracking for one backend instance."""

    # Intentionally in-memory and non-persistent across restarts, like coaching._RateLimiter.
    def __init__(self, limit_usd: float) -> None:
        self.limit_usd = limit_usd
        self._lock = Lock()
        self._month_key: str | None = None
        self._spent_usd = 0.0

    def has_room(self, now: datetime) -> bool:
        with self._lock:
            self._reset_if_new_month(now)
            return self._spent_usd < self.limit_usd

    def record_cost(self, usd: float, now: datetime) -> None:
        with self._lock:
            self._reset_if_new_month(now)
            self._spent_usd += usd

    def resets_at(self, now: datetime) -> datetime:
        utc_now = now.astimezone(UTC)
        if utc_now.month == 12:
            return datetime(utc_now.year + 1, 1, 1, tzinfo=UTC)
        return datetime(utc_now.year, utc_now.month + 1, 1, tzinfo=UTC)

    def _reset_if_new_month(self, now: datetime) -> None:
        month_key = now.astimezone(UTC).strftime("%Y-%m")
        if month_key != self._month_key:
            self._month_key = month_key
            self._spent_usd = 0.0


def _draft_grading_budget() -> DraftGradingBudget:
    try:
        limit = float(os.environ.get(
            "SMALLTALK_DRAFT_GRADING_MONTHLY_BUDGET_USD", _DEFAULT_MONTHLY_BUDGET_USD
        ))
    except (TypeError, ValueError):
        limit = _DEFAULT_MONTHLY_BUDGET_USD
    if not math.isfinite(limit) or limit <= 0:
        limit = _DEFAULT_MONTHLY_BUDGET_USD
    return DraftGradingBudget(limit)


def _value(source: object, key: str) -> object:
    return source.get(key) if isinstance(source, dict) else getattr(source, key, None)


def _cost_for_usage(response: Any) -> float:
    usage = _value(response, "usage")
    input_tokens = _value(usage, "input_tokens")
    output_tokens = _value(usage, "output_tokens")
    input_count = input_tokens if isinstance(input_tokens, int) and not isinstance(input_tokens, bool) else 0
    output_count = output_tokens if isinstance(output_tokens, int) and not isinstance(output_tokens, bool) else 0
    return input_count * _INPUT_COST_PER_TOKEN_USD + output_count * _OUTPUT_COST_PER_TOKEN_USD


def _payload_from_response(response: Any) -> object:
    if isinstance(response, dict):
        if response.get("stop_reason") == "refusal":
            raise DraftGradingRefusedError()
        if "content" in response:
            content = response["content"]
            if isinstance(content, list) and content and isinstance(content[0], dict) and isinstance(content[0].get("text"), str):
                return json.loads(content[0]["text"])
        return response
    if getattr(response, "stop_reason", None) == "refusal":
        raise DraftGradingRefusedError()
    content = getattr(response, "content", None)
    if not isinstance(content, list) or not content:
        raise ValueError("missing content")
    text = getattr(content[0], "text", None)
    if text is None and isinstance(content[0], dict):
        text = content[0].get("text")
    if not isinstance(text, str):
        raise ValueError("missing json text")
    return json.loads(text)


def _validate_grading(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {"met_criteria", "feedback"}:
        raise ValueError("invalid grading fields")
    met_criteria, feedback = payload["met_criteria"], payload["feedback"]
    if not isinstance(met_criteria, bool) or not isinstance(feedback, str) or not feedback.strip():
        raise ValueError("invalid grading values")
    return {"met_criteria": met_criteria, "feedback": feedback}


def _grading_attempts() -> int:
    try:
        attempts = int(os.environ.get("SMALLTALK_DRAFT_GRADING_ATTEMPTS", _DEFAULT_GRADING_ATTEMPTS))
    except (TypeError, ValueError):
        return _DEFAULT_GRADING_ATTEMPTS
    return attempts if 1 <= attempts <= 5 else _DEFAULT_GRADING_ATTEMPTS


def _invalid_response_reason(error: Exception) -> str:
    if isinstance(error, json.JSONDecodeError):
        return error.msg
    if isinstance(error, ValueError):
        return str(error)
    return type(error).__name__


def grade_draft(
    adapter: DraftGradingAdapter,
    budget: DraftGradingBudget,
    prompt: str,
    good_answer_demonstrates: str,
    draft: str,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Make one bounded feedback operation and meter every obtained response."""
    moment = now or datetime.now(UTC)
    if not budget.has_room(moment):
        raise BudgetExceededError()

    attempts = _grading_attempts()
    for attempt in range(1, attempts + 1):
        try:
            response = adapter.request(prompt, good_answer_demonstrates, draft)
            budget.record_cost(_cost_for_usage(response), moment)
            return _validate_grading(_payload_from_response(response))
        except DraftGradingRefusedError:
            raise
        except anthropic.APIStatusError as error:
            status = error.status_code
            if status < 500 and status != 429:
                LOGGER.error("draft grading provider_error=%s", status)
                raise DraftGradingError() from error
            LOGGER.error("draft grading attempt=%d/%d provider_error=%s", attempt, attempts, status)
            if attempt == attempts:
                LOGGER.error("draft grading exhausted attempts=%d", attempts)
                raise DraftGradingError() from error
        except (anthropic.APIConnectionError, anthropic.APITimeoutError) as error:
            LOGGER.error(
                "draft grading attempt=%d/%d provider_error=%s",
                attempt, attempts, type(error).__name__,
            )
            if attempt == attempts:
                LOGGER.error("draft grading exhausted attempts=%d", attempts)
                raise DraftGradingError() from error
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
            LOGGER.error(
                "draft grading attempt=%d/%d invalid_response reason=%s",
                attempt, attempts, _invalid_response_reason(error),
            )
            if attempt == attempts:
                LOGGER.error("draft grading exhausted attempts=%d", attempts)
                raise DraftGradingError() from error
    raise DraftGradingError()
