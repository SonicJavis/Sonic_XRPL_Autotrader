from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from sonic_xrpl.outcomes.models import PaperOutcomeAttribution, SignalFeedbackSummary


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def write_outcome_report(
    attributions: list[PaperOutcomeAttribution],
    output_dir: str | Path,
) -> tuple[str, str]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "phase51_paper_outcomes.json"
    md_path = output / "phase51_paper_outcomes.md"

    payload = {
        "phase": 51,
        "paper_only": True,
        "live_execution_allowed": False,
        "attributions": [_jsonable(item) for item in attributions],
    }
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    lines = ["# Phase 51 Paper Outcome Attribution", "", "Paper only: yes", "Live execution allowed: false", "", "## Attributions"]
    if not attributions:
        lines.append("- No attributions available.")
    for item in attributions:
        lines.append(
            f"- {item.candidate_id}: {item.signal_type} -> {item.outcome_label.value} "
            f"({item.observed_return_bps} bps, window={item.window})"
        )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return str(json_path), str(md_path)


def write_feedback_report(
    feedback: SignalFeedbackSummary,
    output_dir: str | Path,
) -> tuple[str, str]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "phase51_signal_feedback.json"
    md_path = output / "phase51_signal_feedback.md"

    json_path.write_text(json.dumps(_jsonable(feedback), indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# Phase 51 Signal Feedback",
        "",
        f"Feedback ID: {feedback.feedback_id}",
        f"Total attributed: {feedback.total_attributed}",
        f"Wins: {feedback.wins}",
        f"Losses: {feedback.losses}",
        f"Flats: {feedback.flats}",
        f"Missing observations: {feedback.missing_observations}",
        "",
        "## Buckets",
    ]
    for bucket in feedback.by_signal_type.values():
        lines.append(
            f"- {bucket.signal_type}: count={bucket.count}, wins={bucket.wins}, "
            f"losses={bucket.losses}, avg={bucket.average_observed_return_bps} bps"
        )
    lines.append("")
    lines.append("## Recommendations")
    for recommendation in feedback.recommendations:
        lines.append(f"- {recommendation}")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return str(json_path), str(md_path)
