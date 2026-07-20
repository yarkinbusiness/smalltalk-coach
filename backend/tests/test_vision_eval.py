from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from backend.app.transcript import UnreadableTranscriptError
from backend.eval import vision_eval


REPO_ROOT = Path(__file__).resolve().parents[2]


class FakeVisionAdapter:
    def __init__(self, response: object) -> None:
        self.response = response

    def request(self, *, media_type: str, image_base64: str, user_message_side: str) -> object:
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def _case(tmp_path: Path, expected_turns: list[dict[str, str]]) -> vision_eval.EvalCase:
    image_path = tmp_path / "case.png"
    image_path.write_bytes(b"not inspected by the fake adapter")
    return vision_eval.EvalCase(
        case_id="case", image_path=image_path, media_type="image/png",
        user_message_side="right", expected_turns=tuple(expected_turns),
        mock_path=tmp_path / "case.mock.json",
    )


def _payload(turns: list[tuple[str, str]]) -> dict[str, object]:
    return {
        "schema_version": 1,
        "source_kind": "screenshot",
        "user_speaker_id": "user",
        "turns": [
            {"index": index, "speaker_id": speaker, "speaker": speaker, "text": text, "source": "vision"}
            for index, (speaker, text) in enumerate(turns)
        ],
    }


def _score(tmp_path: Path, expected: list[dict[str, str]], extracted: list[tuple[str, str]]) -> vision_eval.CaseScore:
    return vision_eval.evaluate_case(_case(tmp_path, expected), FakeVisionAdapter(_payload(extracted)))


def test_perfect_extraction_scores_all_metrics_and_passes(tmp_path: Path) -> None:
    expected = [
        {"speaker": "other", "text": "Are you free after work?"},
        {"speaker": "user", "text": "Yes, I can meet then."},
    ]
    score = _score(tmp_path, expected, [("other", expected[0]["text"]), ("user", expected[1]["text"])])

    assert (score.recall, score.fidelity, score.order, score.attribution) == (1.0, 1.0, 1.0, 1.0)
    assert score.passed


def test_missing_expected_turn_drops_recall_below_threshold(tmp_path: Path) -> None:
    expected = [
        {"speaker": "other", "text": "First question"},
        {"speaker": "user", "text": "First answer"},
        {"speaker": "other", "text": "Second question"},
    ]
    score = _score(tmp_path, expected, [("other", "First question"), ("user", "First answer")])

    assert score.recall < vision_eval.Thresholds().recall
    assert not score.passed


def test_fidelity_attribution_and_order_fail_independently(tmp_path: Path) -> None:
    expected = [
        {"speaker": "other", "text": "Could we meet for lunch tomorrow at the cafe?"},
        {"speaker": "user", "text": "That sounds lovely to me."},
        {"speaker": "other", "text": "I will reserve a table."},
    ]

    fidelity = _score(tmp_path, expected, [
        ("other", "Could lunch work at cafe?"),
        ("user", expected[1]["text"]),
        ("other", expected[2]["text"]),
    ])
    assert fidelity.recall == fidelity.order == fidelity.attribution == 1.0
    assert fidelity.fidelity < vision_eval.Thresholds().fidelity
    assert not fidelity.passed

    attribution = _score(tmp_path, expected, [
        ("user", expected[0]["text"]),
        ("user", expected[1]["text"]),
        ("other", expected[2]["text"]),
    ])
    assert attribution.recall == attribution.fidelity == attribution.order == 1.0
    assert attribution.attribution < vision_eval.Thresholds().attribution
    assert not attribution.passed

    order = _score(tmp_path, expected, [
        ("user", expected[1]["text"]),
        ("other", expected[0]["text"]),
        ("other", expected[2]["text"]),
    ])
    assert order.recall == order.fidelity == order.attribution == 1.0
    assert order.order < vision_eval.Thresholds().order
    assert not order.passed


def test_extraction_failure_scores_zero_and_records_category(tmp_path: Path) -> None:
    case = _case(tmp_path, [{"speaker": "other", "text": "Hello there"}])
    score = vision_eval.evaluate_case(case, FakeVisionAdapter(UnreadableTranscriptError("unreadable")))

    assert (score.recall, score.fidelity, score.order, score.attribution) == (0.0, 0.0, 0.0, 0.0)
    assert score.failure_category == "unreadable_transcript"
    assert not score.passed


def test_live_mode_is_gated_before_adapter_construction() -> None:
    synthetic_cases = REPO_ROOT / "backend" / "eval" / "vision_cases" / "synthetic"

    def adapter_factory() -> object:
        raise AssertionError("live adapter must not be constructed")

    exit_code = vision_eval.main(
        ["--cases", str(synthetic_cases)], adapter_factory=adapter_factory, environ={},
    )
    assert exit_code == 2


def test_mock_cli_synthetic_cases_writes_redacted_report(tmp_path: Path) -> None:
    synthetic_cases = REPO_ROOT / "backend" / "eval" / "vision_cases" / "synthetic"
    report_path = tmp_path / "report.json"

    process = subprocess.run(
        [
            sys.executable, "-m", "backend.eval.vision_eval", "--cases", str(synthetic_cases),
            "--mock", "--out", str(report_path),
        ],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert process.returncode == 1
    assert "synthetic-01" in process.stdout and "PASS" in process.stdout
    assert "synthetic-02" in process.stdout and "FAIL" in process.stdout
    assert [case["case_id"] for case in report["cases"]] == ["synthetic-01", "synthetic-02"]
    assert all("expected_turns" not in case and "extracted_turns" not in case for case in report["cases"])
    assert report["cases"][0]["passed"] is True
    assert report["cases"][1]["passed"] is False
