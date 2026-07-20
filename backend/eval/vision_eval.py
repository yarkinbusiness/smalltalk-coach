"""Evaluate screenshot transcript extraction against consented local cases."""

from __future__ import annotations

import argparse
import base64
import difflib
import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from backend.app.diagnosis import CoachingRefusedError
from backend.app.transcript import UnreadableTranscriptError
from backend.app.vision import AnthropicVisionAdapter, VisionError, extract_transcript


MATCH_RATIO = 0.60


class UsageError(ValueError):
    """Raised for invalid eval inputs or an intentionally blocked live run."""


@dataclass(frozen=True)
class Thresholds:
    recall: float = 0.95
    fidelity: float = 0.90
    order: float = 1.0
    attribution: float = 1.0


@dataclass(frozen=True)
class EvalCase:
    case_id: str
    image_path: Path
    media_type: str
    user_message_side: str
    expected_turns: tuple[dict[str, str], ...]
    mock_path: Path


@dataclass(frozen=True)
class CaseScore:
    case_id: str
    recall: float
    fidelity: float
    order: float
    attribution: float
    passed: bool
    failure_category: str | None = None
    expected_turns: tuple[dict[str, str], ...] | None = None
    extracted_turns: tuple[dict[str, str], ...] | None = None


class MockVisionAdapter:
    """Return one raw extractor response without creating a provider client."""

    def __init__(self, response: object) -> None:
        self._response = response

    def request(self, *, media_type: str, image_base64: str, user_message_side: str) -> object:
        return self._response


def _normalized_text(value: str) -> str:
    return " ".join(value.casefold().split())


def _ratio(expected: str, actual: str) -> float:
    return difflib.SequenceMatcher(None, _normalized_text(expected), _normalized_text(actual)).ratio()


def _validate_expected_turns(value: object, side: str, path: Path) -> tuple[dict[str, str], ...]:
    if not isinstance(value, list) or not value:
        raise UsageError(f"{path}: expected_turns must be a non-empty list")
    turns: list[dict[str, str]] = []
    for turn in value:
        if not isinstance(turn, dict) or set(turn) != {"speaker", "text"}:
            raise UsageError(f"{path}: each expected turn must contain only speaker and text")
        speaker, text = turn["speaker"], turn["text"]
        if speaker not in {"user", "other"} or not isinstance(text, str) or not text.strip():
            raise UsageError(f"{path}: invalid expected turn")
        turns.append({"speaker": speaker, "text": text.strip()})
    if side == "unknown" and any(turn["speaker"] != "other" for turn in turns):
        raise UsageError(f"{path}: unknown-side cases must expect only other turns")
    return tuple(turns)


def load_cases(cases_dir: Path) -> list[EvalCase]:
    """Load case metadata without reading image bytes."""
    if not cases_dir.is_dir():
        raise UsageError(f"cases directory does not exist: {cases_dir}")
    sidecars = sorted(cases_dir.glob("*.expected.json"))
    if not sidecars:
        raise UsageError(f"no .expected.json cases found in: {cases_dir}")
    cases: list[EvalCase] = []
    seen_ids: set[str] = set()
    for sidecar in sidecars:
        try:
            payload = json.loads(sidecar.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise UsageError(f"cannot read case metadata: {sidecar}") from error
        if not isinstance(payload, dict):
            raise UsageError(f"{sidecar}: metadata must be an object")
        required = {"case_id", "image", "media_type", "user_message_side", "expected_turns"}
        allowed = required | {"notes"}
        if set(payload) - allowed or not required <= set(payload):
            raise UsageError(f"{sidecar}: invalid case fields")
        case_id = payload["case_id"]
        image_name = payload["image"]
        media_type = payload["media_type"]
        side = payload["user_message_side"]
        if not isinstance(case_id, str) or not case_id or case_id in seen_ids:
            raise UsageError(f"{sidecar}: case_id must be unique and non-empty")
        if not isinstance(image_name, str) or Path(image_name).name != image_name:
            raise UsageError(f"{sidecar}: image must be a file name in the cases directory")
        if not isinstance(media_type, str) or not media_type.startswith("image/"):
            raise UsageError(f"{sidecar}: media_type must be an image type")
        if side not in {"left", "right", "unknown"}:
            raise UsageError(f"{sidecar}: invalid user_message_side")
        image_path = cases_dir / image_name
        if not image_path.is_file():
            raise UsageError(f"{sidecar}: referenced image does not exist")
        expected_turns = _validate_expected_turns(payload["expected_turns"], side, sidecar)
        seen_ids.add(case_id)
        cases.append(EvalCase(
            case_id=case_id,
            image_path=image_path,
            media_type=media_type,
            user_message_side=side,
            expected_turns=expected_turns,
            mock_path=cases_dir / f"{case_id}.mock.json",
        ))
    return cases


def _matches(expected_turns: Sequence[dict[str, str]], extracted_turns: Sequence[dict[str, Any]]) -> list[tuple[int, int, float]]:
    """Greedily match each expected turn to the best unused extracted turn."""
    used: set[int] = set()
    matches: list[tuple[int, int, float]] = []
    for expected_index, expected in enumerate(expected_turns):
        candidates = [
            (index, _ratio(expected["text"], str(turn.get("text", ""))))
            for index, turn in enumerate(extracted_turns)
            if index not in used
        ]
        if not candidates:
            continue
        extracted_index, ratio = max(candidates, key=lambda item: (item[1], -item[0]))
        if ratio >= MATCH_RATIO:
            used.add(extracted_index)
            matches.append((expected_index, extracted_index, ratio))
    return matches


def _score_turns(
    case: EvalCase, extracted_turns: Sequence[dict[str, Any]], thresholds: Thresholds,
) -> CaseScore:
    matches = _matches(case.expected_turns, extracted_turns)
    match_count = len(matches)
    recall = match_count / len(case.expected_turns)
    fidelity = sum(match[2] for match in matches) / match_count if matches else 0.0
    extracted_indices = [match[1] for match in matches]
    if not matches:
        order = 0.0
    elif all(left < right for left, right in zip(extracted_indices, extracted_indices[1:])):
        order = 1.0
    else:
        order = sum(left < right for left, right in zip(extracted_indices, extracted_indices[1:])) / (match_count - 1)
    attribution = (
        sum(
            extracted_turns[extracted_index].get("speaker") == case.expected_turns[expected_index]["speaker"]
            for expected_index, extracted_index, _ in matches
        ) / match_count
        if matches else 0.0
    )
    passed = (
        recall >= thresholds.recall
        and fidelity >= thresholds.fidelity
        and order >= thresholds.order
        and attribution >= thresholds.attribution
    )
    return CaseScore(
        case_id=case.case_id, recall=recall, fidelity=fidelity, order=order,
        attribution=attribution, passed=passed,
        expected_turns=case.expected_turns,
        extracted_turns=tuple(
            {"speaker": str(turn["speaker"]), "text": str(turn["text"])} for turn in extracted_turns
        ),
    )


def _failure_category(error: Exception) -> str:
    if isinstance(error, UnreadableTranscriptError):
        return "unreadable_transcript"
    if isinstance(error, CoachingRefusedError):
        return "refusal"
    if isinstance(error, VisionError):
        return "vision_error"
    return "vision_error"


def evaluate_case(case: EvalCase, adapter: object, thresholds: Thresholds = Thresholds()) -> CaseScore:
    """Extract and score one case; expected or extracted text stays in memory only."""
    try:
        image_base64 = base64.b64encode(case.image_path.read_bytes()).decode("ascii")
        transcript = extract_transcript(
            adapter, media_type=case.media_type, image_base64=image_base64,
            user_message_side=case.user_message_side,
        )
    except (UnreadableTranscriptError, VisionError, CoachingRefusedError) as error:
        return CaseScore(
            case_id=case.case_id, recall=0.0, fidelity=0.0, order=0.0,
            attribution=0.0, passed=False, failure_category=_failure_category(error),
        )
    return _score_turns(case, transcript["turns"], thresholds)


def _load_mock_adapter(case: EvalCase) -> MockVisionAdapter:
    try:
        payload = json.loads(case.mock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise UsageError(f"cannot read mock response: {case.mock_path}") from error
    return MockVisionAdapter(payload)


def ensure_live_allowed(environ: Mapping[str, str] | None = None) -> None:
    """Require an explicit opt-in before any live adapter is created."""
    environment = os.environ if environ is None else environ
    if environment.get("SMALLTALK_VISION_EVAL") != "1" or not environment.get("ANTHROPIC_API_KEY"):
        raise UsageError(
            "live vision eval is blocked: set SMALLTALK_VISION_EVAL=1 and ANTHROPIC_API_KEY"
        )


def evaluate_cases(
    cases: Sequence[EvalCase], *, mock: bool, thresholds: Thresholds,
    adapter_factory: Callable[[], object] = AnthropicVisionAdapter,
    environ: Mapping[str, str] | None = None,
) -> list[CaseScore]:
    if mock:
        return [evaluate_case(case, _load_mock_adapter(case), thresholds) for case in cases]
    ensure_live_allowed(environ)
    adapter = adapter_factory()
    return [evaluate_case(case, adapter, thresholds) for case in cases]


def _aggregate(scores: Sequence[CaseScore]) -> dict[str, float | int]:
    count = len(scores)
    return {
        "recall": sum(score.recall for score in scores) / count,
        "fidelity": sum(score.fidelity for score in scores) / count,
        "order": sum(score.order for score in scores) / count,
        "attribution": sum(score.attribution for score in scores) / count,
        "passed": sum(score.passed for score in scores),
        "failed": sum(not score.passed for score in scores),
    }


def report_data(scores: Sequence[CaseScore], *, include_text: bool) -> dict[str, object]:
    cases: list[dict[str, object]] = []
    for score in scores:
        item = asdict(score)
        if not include_text:
            item.pop("expected_turns")
            item.pop("extracted_turns")
        cases.append(item)
    return {"cases": cases, "aggregate": _aggregate(scores)}


def _print_report(scores: Sequence[CaseScore]) -> None:
    print("case_id\t recall\t fidelity\t order\t attribution\t result\t failure")
    for score in scores:
        print(
            f"{score.case_id}\t {score.recall:.2f}\t {score.fidelity:.2f}\t "
            f"{score.order:.2f}\t {score.attribution:.2f}\t "
            f"{'PASS' if score.passed else 'FAIL'}\t {score.failure_category or '-'}"
        )
    aggregate = _aggregate(scores)
    print(
        "aggregate\t "
        f"{aggregate['recall']:.2f}\t {aggregate['fidelity']:.2f}\t "
        f"{aggregate['order']:.2f}\t {aggregate['attribution']:.2f}\t "
        f"{aggregate['passed']} passed, {aggregate['failed']} failed"
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate screenshot transcript extraction cases.")
    parser.add_argument("--cases", required=True, type=Path, help="Directory containing case metadata and images.")
    parser.add_argument("--mock", action="store_true", help="Use each case's local canned response.")
    parser.add_argument("--out", type=Path, help="Write the JSON score report to this path.")
    parser.add_argument("--include-text", action="store_true", help="Include expected and extracted transcript text in --out.")
    parser.add_argument("--recall-threshold", type=float, default=0.95)
    parser.add_argument("--fidelity-threshold", type=float, default=0.90)
    parser.add_argument("--order-threshold", type=float, default=1.0)
    parser.add_argument("--attribution-threshold", type=float, default=1.0)
    return parser


def _thresholds_from_args(args: argparse.Namespace) -> Thresholds:
    values = {
        "recall": args.recall_threshold,
        "fidelity": args.fidelity_threshold,
        "order": args.order_threshold,
        "attribution": args.attribution_threshold,
    }
    if any(not 0.0 <= value <= 1.0 for value in values.values()):
        raise UsageError("all thresholds must be between 0 and 1")
    return Thresholds(**values)


def main(argv: Sequence[str] | None = None, *, adapter_factory: Callable[[], object] = AnthropicVisionAdapter,
         environ: Mapping[str, str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        thresholds = _thresholds_from_args(args)
        cases = load_cases(args.cases)
        scores = evaluate_cases(
            cases, mock=args.mock, thresholds=thresholds,
            adapter_factory=adapter_factory, environ=environ,
        )
        _print_report(scores)
        if args.out is not None:
            args.out.write_text(json.dumps(report_data(scores, include_text=args.include_text), indent=2) + "\n", encoding="utf-8")
        return 0 if all(score.passed for score in scores) else 1
    except UsageError as error:
        print(f"vision eval: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
