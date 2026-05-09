from __future__ import annotations

import json
from pathlib import Path

from sonic_xrpl.calibration_review.models import (
    CalibrationReviewReport,
    CalibrationReadinessResult,
    ThresholdRecommendation,
    jsonable,
)
from sonic_xrpl.signals.evidence import stable_id


SAFETY_STATEMENT = (
    "Phase 53 calibration readiness reports are offline, paper-only, human-review-only artifacts. "
    "Recommendations are advisory only and do not mutate runtime configuration. Live execution remains blocked."
)
ACCURACY_STATEMENT = (
    "Fixture outcomes are not executable fill claims, not profitability evidence, and not execution approval. "
    "Synthetic evidence can test code paths but cannot support calibration readiness."
)


def build_review_report(
    readiness_result: CalibrationReadinessResult,
    recommendations: tuple[ThresholdRecommendation, ...],
    generated_files: dict[str, str] | None = None,
) -> CalibrationReviewReport:
    report_id = stable_id(
        "crp",
        readiness_result.readiness_id,
        tuple(item.recommendation_id for item in recommendations),
        SAFETY_STATEMENT,
        ACCURACY_STATEMENT,
    )
    return CalibrationReviewReport(
        report_id=report_id,
        readiness_result=readiness_result,
        recommendations=recommendations,
        safety_statement=SAFETY_STATEMENT,
        accuracy_statement=ACCURACY_STATEMENT,
        generated_files=generated_files or {},
        paper_only=True,
        live_execution_allowed=False,
    )


def _markdown(report: CalibrationReviewReport) -> str:
    result = report.readiness_result
    snapshot = result.evidence_snapshot
    lines = [
        "# Phase 53 Calibration Readiness Review",
        "",
        f"Report ID: `{report.report_id}`",
        f"Readiness ID: `{result.readiness_id}`",
        f"Status: `{result.status}`",
        f"Confidence: `{result.confidence}`",
        f"Paper only: `{str(report.paper_only).lower()}`",
        f"Live execution allowed: `{str(report.live_execution_allowed).lower()}`",
        "",
        "## Evidence Summary",
        f"- Signals: {snapshot.signal_count}",
        f"- Reviews: {snapshot.review_count}",
        f"- Paper decisions: {snapshot.paper_decision_count}",
        f"- Paper intents: {snapshot.paper_intent_count}",
        f"- Attributed outcomes: {snapshot.attributed_outcome_count}",
        f"- Corpus cases: {snapshot.corpus_case_count}",
        f"- Source-backed cases: {snapshot.source_backed_case_count}",
        f"- Synthetic cases: {snapshot.synthetic_case_count}",
        f"- Missing observations: {snapshot.missing_observation_count}",
        f"- Invalid observations: {snapshot.invalid_observation_count}",
        "",
        "## Blockers",
        *(f"- {item}" for item in (result.blockers or ("none",))),
        "",
        "## Warnings",
        *(f"- {item}" for item in (result.warnings or ("none",))),
        "",
        "## Recommendations",
        "| Target | Direction | Confidence | Rationale |",
        "|---|---:|---:|---|",
        *(
            f"| `{item.target}` | `{item.direction}` | {item.confidence} | {item.rationale} |"
            for item in report.recommendations
        ),
        "",
        "## Provenance",
        *(f"- `{item}`" for item in (snapshot.provenance_refs or snapshot.source_files)),
        "",
        "## Safety",
        report.safety_statement,
        "",
        "## Accuracy",
        report.accuracy_statement,
        "",
        "## Rollback",
        "Revert the Phase 53 merge commit. No database migration, external service setup, live config, or secrets are introduced.",
        "",
    ]
    return "\n".join(lines)


def write_calibration_review_report(
    readiness_result: CalibrationReadinessResult,
    recommendations: tuple[ThresholdRecommendation, ...],
    output_dir: str | Path = "reports/phase53",
) -> CalibrationReviewReport:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    report = build_review_report(readiness_result, recommendations)
    json_path = target / "calibration_readiness.json"
    md_path = target / "calibration_readiness.md"
    recommendations_path = target / "calibration_recommendations.json"
    json_path.write_text(json.dumps(jsonable(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(_markdown(report), encoding="utf-8")
    recommendations_path.write_text(
        json.dumps([jsonable(item) for item in recommendations], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    generated = {
        "readiness_json": str(json_path),
        "readiness_markdown": str(md_path),
        "recommendations_json": str(recommendations_path),
    }
    return build_review_report(readiness_result, recommendations, generated)
