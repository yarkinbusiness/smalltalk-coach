"""Pure-function edge cases for coach._extract_report — no Anthropic client
needed at all, this only exercises string/JSON parsing logic.

_extract_report scans agent_messages from last to first and returns the
first one that (after optional fence-stripping) parses as JSON containing
both "scores" and "focus_areas" keys; otherwise it falls back to a
parse_error payload carrying the last raw message.
"""

import json

from app import coach


def test_extract_report_parses_fenced_json_block_with_json_tag():
    # This covers the whole-message-is-a-fence case; see
    # test_extract_report_prose_then_fenced_block_is_unwrapped below for the
    # prose-then-fence case (also handled, via _strip_fence's regex fallback).
    report = {"scores": {"warmth": 4}, "focus_areas": ["Ask more follow-ups"]}
    messages = ["```json\n" + json.dumps(report) + "\n```"]

    result = coach._extract_report(messages)

    assert result == report


def test_extract_report_prose_then_fenced_block_is_unwrapped():
    """Previously a real gap: if a single message leads with prose and only
    THEN opens a fenced block, the old fence-stripping branch (which only
    fired when the *entire* message started with "```") missed it and fell
    through to the parse_error fallback. _strip_fence now also searches for
    a fenced block anywhere in the message, so this unwraps correctly."""
    report = {"scores": {"warmth": 4}, "focus_areas": ["Ask more follow-ups"]}
    messages = ["Here's the report:\n```json\n" + json.dumps(report) + "\n```"]

    result = coach._extract_report(messages)

    assert result == report


def test_extract_report_parses_fenced_block_without_json_tag():
    report = {"scores": {"warmth": 3}, "focus_areas": []}
    messages = ["```\n" + json.dumps(report) + "\n```"]

    result = coach._extract_report(messages)

    assert result == report


def test_extract_report_parses_prose_then_final_json_message():
    """The coordinator 'thinks out loud' in earlier messages, then emits the
    final JSON blob as its last message — the common real case."""
    report = {"scores": {"warmth": 5}, "focus_areas": ["y"]}
    messages = [
        "Let me review the transcript turn by turn first...",
        "Okay, I've weighed the four graders' notes.",
        json.dumps(report),
    ]

    result = coach._extract_report(messages)

    assert result == report


def test_extract_report_skips_trailing_non_json_chatter():
    """If the LAST message is non-JSON commentary but an earlier one has the
    valid report, the backward scan should still find it."""
    report = {"scores": {"warmth": 2}, "focus_areas": ["z"]}
    messages = [json.dumps(report), "Let me know if you want me to expand on that."]

    result = coach._extract_report(messages)

    assert result == report


def test_extract_report_json_missing_required_keys_falls_through():
    messages = [json.dumps({"foo": "bar"})]

    result = coach._extract_report(messages)

    assert result["parse_error"] is True
    assert result["raw"] == messages[-1]
    assert result["scores"] == {}
    assert result["focus_areas"] == []


def test_extract_report_garbage_that_never_parses():
    messages = ["not json at all", "{still not valid json"]

    result = coach._extract_report(messages)

    assert result == {
        "scores": {},
        "strengths": [],
        "focus_areas": [],
        "drill_suggestion": "",
        "raw": messages[-1],
        "parse_error": True,
    }


def test_extract_report_empty_message_list():
    result = coach._extract_report([])

    assert result["parse_error"] is True
    assert result["raw"] == ""
