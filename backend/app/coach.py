"""Runs the coach_coordinator as a real CMA session — the one place in this
app where a sandboxed session actually earns its cost (see ARCHITECTURE.md:
"A deliberate split"). One session per ended practice conversation.
"""

import json
import math
import re

from anthropic import Anthropic

# The four graded dimensions the multi-worker roster produces (warmth_worker,
# curiosity_worker, reciprocity_worker, flow_worker — see agents_setup.py).
REPORT_DIMENSIONS = ("warmth", "curiosity", "reciprocity", "flow")
SCORE_MIN, SCORE_MAX = 1, 5

# Matches a fenced code block anywhere in a message, optionally tagged
# ```json, e.g. "Here's the report:\n```json\n{...}\n```" — used to unwrap
# case (2) below, the gap the fence-stripping in _extract_report used to miss.
_FENCE_RE = re.compile(r"```(?:json)?\s*\n?(.*?)```", re.IGNORECASE | re.DOTALL)


def _transcript_to_text(transcript: list[dict]) -> str:
    lines = [f"{turn['role'].upper()}: {turn['text']}" for turn in transcript]
    return "\n".join(lines)


def _strip_fence(text: str) -> str:
    """Best-effort Markdown code-fence removal, handling three shapes seen
    from the coordinator:
      1. The whole message IS a fenced block (optionally ```json-tagged).
      2. Prose precedes a fenced block somewhere later in the message (the
         previously-unhandled gap — a message like "Here's the report:\\n
         ```json\\n{...}\\n```" used to fall straight through to the
         parse_error fallback because the old check only fired when the
         *entire* message started with "```").
      3. No fence at all — returned unchanged (the common "just JSON" case).
    """
    stripped = text.strip()
    if stripped.startswith("```"):
        inner = stripped.strip("`")
        return inner.split("\n", 1)[-1] if inner.lower().startswith("json") else inner
    match = _FENCE_RE.search(stripped)
    if match:
        return match.group(1).strip()
    return stripped


def _extract_report(agent_messages: list[str]) -> dict:
    """The coordinator is asked for one final JSON blob; it may still think
    out loud first. Take the last message that parses as the expected shape."""
    for text in reversed(agent_messages):
        candidate = _strip_fence(text)
        try:
            parsed = json.loads(candidate)
            if "scores" in parsed and "focus_areas" in parsed:
                return parsed
        except json.JSONDecodeError:
            continue
    return {
        "scores": {},
        "strengths": [],
        "focus_areas": [],
        "drill_suggestion": "",
        "raw": agent_messages[-1] if agent_messages else "",
        "parse_error": True,
    }


def _coerce_score(value) -> int | None:
    """Best-effort coercion of a single dimension's score to an int clamped
    to [SCORE_MIN, SCORE_MAX]. Returns None when `value` can't be read as a
    number at all (non-numeric garbage) so the caller can drop the key
    entirely instead of inventing a fake grade."""
    if isinstance(value, bool):
        # bool is a subclass of int in Python — treat True/False as garbage
        # rather than silently scoring 1/0.
        return None
    if isinstance(value, (int, float)):
        num = float(value)
    elif isinstance(value, str):
        try:
            num = float(value.strip())
        except ValueError:
            return None
    else:
        return None
    if not math.isfinite(num):
        return None
    return max(SCORE_MIN, min(SCORE_MAX, round(num)))


def _coerce_str_list(value) -> list[str]:
    """Coerce `strengths`/`focus_areas` into list[str]. A bare string is
    treated as a single-item list (a plausible coordinator slip — emitting a
    string where a list was expected). Any other non-list, non-string value
    (int, dict, None, ...) becomes an empty list rather than raising."""
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    return []


def _coerce_optional_str(value) -> str | None:
    if value is None:
        return None
    return value if isinstance(value, str) else str(value)


def normalize_report(raw: dict) -> dict:
    """Coerce whatever `_extract_report` produced into a shape that reliably
    satisfies the `CoachReport` pydantic model (schemas.py) — never raises,
    regardless of how malformed `raw` is.

    Normalization policy (documented explicitly, not just implied by code):

    - Fundamentally unparseable input takes priority over everything else.
      This covers: `raw` isn't even a dict; `raw` already carries
      `parse_error: True` (i.e. it's already `_extract_report`'s own
      fallback shape — re-normalizing it is a no-op, we just carry its
      `raw` text forward); or `raw` is missing the top-level `scores` or
      `focus_areas` key entirely (the same two-key gate `_extract_report`
      itself uses to decide a message "looks like" a report at all). Any of
      these degrade cleanly to the canonical parse_error shape rather than
      trying to salvage structure out of something that was never a report.

    - scores: each of the four known dimensions (warmth, curiosity,
      reciprocity, flow) is read independently and coerced to `int`,
      clamped to 1-5 — handles real ints, floats (e.g. 4.5 -> 4, rounded
      half-to-even then clamped), and numeric strings (e.g. "4"). A
      dimension key that is *missing* from the input is simply omitted
      from the output dict, not defaulted to a sentinel value — CoachReport
      never invents a numeric grade no grader actually produced, and both
      the pydantic model (`scores: dict[str, int]`, no required keys) and
      the iOS `Codable` model (`[String: Int]`) tolerate a partial dict
      fine. A dimension whose value is non-numeric garbage (e.g. "n/a", a
      list, None) is likewise omitted rather than defaulted. Any
      *unexpected extra* key in `scores` (not one of the four known
      dimensions) is silently dropped — we only ever copy the four known
      keys over.

    - strengths / focus_areas: coerced to `list[str]` (see
      `_coerce_str_list`).

    - drill_suggestion: coerced with `str()`; `None`/absent becomes `""`.

    - raw / parse_error: on the success path, `raw` passes through
      unchanged (normally absent/None for a well-formed report) and
      `parse_error` is explicitly set to `False`. Any top-level key on the
      input besides these six is dropped — normalize_report always builds a
      fresh dict of exactly the known CoachReport fields, never a
      passthrough copy of `raw`.
    """
    if (
        not isinstance(raw, dict)
        or raw.get("parse_error")
        or "scores" not in raw
        or "focus_areas" not in raw
    ):
        raw_text = raw.get("raw") if isinstance(raw, dict) else raw
        return {
            "scores": {},
            "strengths": [],
            "focus_areas": [],
            "drill_suggestion": "",
            "raw": _coerce_optional_str(raw_text) or "",
            "parse_error": True,
        }

    raw_scores = raw.get("scores")
    scores: dict[str, int] = {}
    if isinstance(raw_scores, dict):
        for dim in REPORT_DIMENSIONS:
            if dim in raw_scores:
                coerced = _coerce_score(raw_scores[dim])
                if coerced is not None:
                    scores[dim] = coerced
    # A non-dict `scores` container (string, list, ...) yields no scores at
    # all rather than raising — there's nothing sensible to extract from it.

    return {
        "scores": scores,
        "strengths": _coerce_str_list(raw.get("strengths")),
        "focus_areas": _coerce_str_list(raw.get("focus_areas")),
        "drill_suggestion": _coerce_optional_str(raw.get("drill_suggestion")) or "",
        "raw": _coerce_optional_str(raw.get("raw")),
        "parse_error": False,
    }


def run_coaching_session(
    client: Anthropic,
    coordinator_id: str,
    coordinator_version: int,
    environment_id: str,
    memory_store_id: str,
    transcript: list[dict],
) -> dict:
    session = client.beta.sessions.create(
        agent={"type": "agent", "id": coordinator_id, "version": coordinator_version},
        environment_id=environment_id,
        resources=[{"type": "memory_store", "memory_store_id": memory_store_id}],
    )

    agent_messages: list[str] = []
    with client.beta.sessions.events.stream(session.id) as stream:
        client.beta.sessions.events.send(
            session.id,
            events=[
                {
                    "type": "user.message",
                    "content": [
                        {
                            "type": "text",
                            "text": "Grade this small-talk practice transcript and "
                            "return the coaching report JSON.\n\n"
                            + _transcript_to_text(transcript),
                        }
                    ],
                }
            ],
        )
        for event in stream:
            if event.type == "agent.message":
                text = "".join(
                    block.text for block in event.content if getattr(block, "type", None) == "text"
                )
                if text:
                    agent_messages.append(text)
            elif event.type == "session.status_idle":
                break

    return _extract_report(agent_messages)
