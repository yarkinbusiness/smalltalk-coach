"""Normalize pasted coaching text; by default it is the other party's message."""

from __future__ import annotations

import re
from typing import Any


class UnreadableTranscriptError(ValueError):
    """Raised when pasted text cannot form a usable transcript."""


_LABELLED_LINE = re.compile(r"^\s*([^:\n]{1,80}):\s*(.*?)\s*$")
_USER_LABELS = frozenset({"me", "i", "myself", "user"})
_OTHER_LABELS = frozenset({"them", "they", "other", "partner"})


def _speaker_id(label: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", label.casefold()).strip("-")
    return normalized or "unknown"


def normalize_text(text: object) -> dict[str, Any]:
    """Return normalized pasted text; an unlabeled blob is incoming stimulus."""
    if not isinstance(text, str):
        raise UnreadableTranscriptError("text is not usable")
    trimmed = text.strip()
    # A single character has too little reliable conversational context to coach.
    if len(trimmed) < 2:
        raise UnreadableTranscriptError("text is not usable")

    parsed: list[tuple[str, str]] = []
    for line in trimmed.splitlines():
        match = _LABELLED_LINE.match(line)
        if match is None or not match.group(2):
            parsed = []
            break
        parsed.append((match.group(1).strip(), match.group(2).strip()))

    if not parsed:
        return {
            "schema_version": 1,
            "source_kind": "text",
            "user_speaker_id": None,
            "turns": [
                {
                    "index": 0,
                    "speaker_id": "other",
                    "speaker": "other",
                    "text": trimmed,
                    "source": "pasted",
                }
            ],
        }

    user_present = any(label.casefold() in _USER_LABELS for label, _ in parsed)
    turns: list[dict[str, object]] = []
    for index, (label, turn_text) in enumerate(parsed):
        normalized = label.casefold()
        if normalized in _USER_LABELS:
            speaker, speaker_id = "user", "user"
        elif normalized in _OTHER_LABELS or user_present:
            speaker, speaker_id = "other", "other"
        else:
            speaker, speaker_id = "unknown", _speaker_id(label)
        turns.append(
            {
                "index": index,
                "speaker_id": speaker_id,
                "speaker": speaker,
                "text": turn_text,
                "source": "pasted",
            }
        )
    return {
        "schema_version": 1,
        "source_kind": "text",
        "user_speaker_id": "user" if user_present else None,
        "turns": turns,
    }
