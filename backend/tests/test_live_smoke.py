"""Opt-in live smoke test; normal test runs never contact the provider."""

from __future__ import annotations

import os

import pytest

from backend.app.diagnosis import AnthropicDiagnosisAdapter, diagnose
from backend.app.transcript import normalize_text


pytestmark = pytest.mark.skipif(
    os.environ.get("SMALLTALK_LIVE_SMOKE") != "1" or not os.environ.get("ANTHROPIC_API_KEY"),
    reason="requires SMALLTALK_LIVE_SMOKE=1 and ANTHROPIC_API_KEY",
)


def test_live_text_diagnosis_schema_valid() -> None:
    transcript = normalize_text("Me: I joined the book club yesterday.\nThem: What kind of books do you enjoy?")
    diagnosis = diagnose(AnthropicDiagnosisAdapter(), transcript, set())
    assert set(diagnosis["dimensions"]) == {"warmth", "curiosity", "reciprocity", "flow"}
