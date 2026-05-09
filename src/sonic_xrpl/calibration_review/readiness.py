from __future__ import annotations

from dataclasses import dataclass

from sonic_xrpl.calibration_review.loader import SIGNAL_TYPES
from sonic_xrpl.calibration_review.models import (
    CalibrationEvidenceSnapshot,
    CalibrationReadinessResult,
    CalibrationReadinessRule,
)
from sonic_xrpl.signals.evidence import stable_id


@dataclass(frozen=True)
class ReadinessThresholds:
    minimum_corpus_cases: int = 3
    minimum_attributed_outcomes: int = 3
    minimum_source_backed_ratio: float = 0.8
    maximum_missing_observation_ratio: float = 0.25
    minimum_class_count: int = 1


def _rule(name: str, severity: str, passed: bool, reason: str, refs: tuple[str, ...], limitations: tuple[str, ...] = tuple()) -> CalibrationReadinessRule:
    return CalibrationReadinessRule(
        rule_id=stable_id("crr", name, severity, passed, reason, refs, limitations),
        name=name,
        severity=severity,
        passed=passed,
        reason=reason,
        evidence_refs=refs,
        limitations=limitations,
    )


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def evaluate_readiness(
    snapshot: CalibrationEvidenceSnapshot,
    thresholds: ReadinessThresholds | None = None,
) -> CalibrationReadinessResult:
    limits = thresholds or ReadinessThresholds()
    refs = snapshot.source_files
    source_ratio = _ratio(snapshot.source_backed_case_count, snapshot.corpus_case_count)
    missing_ratio = _ratio(snapshot.missing_observation_count, max(snapshot.corpus_case_count, snapshot.attributed_outcome_count))
    sparse_classes = tuple(
        signal_type for signal_type in SIGNAL_TYPES
        if snapshot.signal_type_counts.get(signal_type, 0) < limits.minimum_class_count
    )

    rules = (
        _rule(
            "minimum_corpus_size",
            "blocker",
            snapshot.corpus_case_count >= limits.minimum_corpus_cases,
            f"Corpus cases {snapshot.corpus_case_count}; required {limits.minimum_corpus_cases}.",
            refs,
        ),
        _rule(
            "source_backed_ratio",
            "blocker",
            snapshot.corpus_case_count > 0 and source_ratio >= limits.minimum_source_backed_ratio,
            f"Source-backed ratio {source_ratio:.2f}; required {limits.minimum_source_backed_ratio:.2f}.",
            refs,
        ),
        _rule(
            "missing_observation",
            "warning",
            missing_ratio <= limits.maximum_missing_observation_ratio,
            f"Missing observation ratio {missing_ratio:.2f}; maximum {limits.maximum_missing_observation_ratio:.2f}.",
            refs,
        ),
        _rule(
            "invalid_numeric_observation",
            "blocker",
            snapshot.invalid_observation_count == 0,
            f"Invalid numeric observations: {snapshot.invalid_observation_count}.",
            refs,
        ),
        _rule(
            "outcome_coverage",
            "blocker",
            snapshot.attributed_outcome_count >= limits.minimum_attributed_outcomes,
            f"Attributed outcomes {snapshot.attributed_outcome_count}; required {limits.minimum_attributed_outcomes}.",
            refs,
        ),
        _rule(
            "signal_classification_coverage",
            "warning",
            not sparse_classes,
            "Sparse signal classes: " + (", ".join(sparse_classes) if sparse_classes else "none"),
            refs,
            sparse_classes,
        ),
        _rule(
            "safety_invariants",
            "blocker",
            snapshot.paper_only is True and snapshot.live_execution_allowed is False and not snapshot.live_enabled_records,
            "All reviewed records must remain paper-only with live execution blocked.",
            refs,
            snapshot.live_enabled_records,
        ),
        _rule(
            "synthetic_fixture",
            "blocker",
            snapshot.synthetic_case_count == 0,
            f"Synthetic corpus cases: {snapshot.synthetic_case_count}.",
            refs,
        ),
        _rule(
            "non_mutating_review",
            "blocker",
            True,
            "Review layer is advisory and does not write runtime configuration.",
            refs,
        ),
        _rule(
            "human_review_required",
            "blocker",
            True,
            "Recommendations require human review and are not execution approval.",
            refs,
        ),
        _rule(
            "provenance_consistency",
            "warning",
            bool(snapshot.provenance_refs) and all(str(item).strip() for item in snapshot.provenance_refs),
            "Provenance references must be present for reviewed evidence.",
            snapshot.provenance_refs,
        ),
        _rule(
            "report_reproducibility",
            "blocker",
            snapshot.created_at == "1970-01-01T00:00:00+00:00",
            "Snapshot timestamp must be deterministic for fixture-backed reports.",
            refs,
        ),
    )

    blockers = tuple(rule.reason for rule in rules if not rule.passed and rule.severity == "blocker")
    warnings = tuple(rule.reason for rule in rules if not rule.passed and rule.severity != "blocker")
    blocker_count = len(blockers)
    warning_count = len(warnings)
    passed_count = sum(1 for rule in rules if rule.passed)
    confidence = round(passed_count / len(rules), 2)
    if blocker_count:
        status = "NOT_READY" if blocker_count >= 2 else "NEEDS_MORE_EVIDENCE"
    elif warning_count:
        status = "REVIEW_WITH_CAUTION"
    else:
        status = "READY_FOR_HUMAN_REVIEW"
    readiness_id = stable_id(
        "cr",
        snapshot.snapshot_id,
        status,
        confidence,
        tuple(rule.rule_id for rule in rules),
        blockers,
        warnings,
    )
    return CalibrationReadinessResult(
        readiness_id=readiness_id,
        status=status,
        confidence=confidence,
        rules=rules,
        blockers=blockers,
        warnings=warnings,
        evidence_snapshot=snapshot,
        paper_only=True,
        live_execution_allowed=False,
    )
