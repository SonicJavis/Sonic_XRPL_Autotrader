from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CalibrationErrorSample:
    execution_survivability_error: float
    slippage_underestimation: float
    depth_overestimation: float
    latency_miss_error: float


@dataclass(slots=True)
class CalibrationRecommendation:
    queue_haircut_pct: float
    drift_haircut_pct: float
    latency_ms: int
    snapshot_max_age_ms: int
    confidence_score: float
    reasoning: str


class ConfidenceWeightedCalibrationEngine:
    def recommend(
        self,
        *,
        samples: list[CalibrationErrorSample],
        fundedness_confidence: float,
        sequence_stability: float,
    ) -> CalibrationRecommendation | None:
        sample_count = len(samples)
        if sample_count < 5:
            return None

        sample_confidence = max(0.0, min(1.0, sample_count / 30.0))
        fundedness = max(0.0, min(1.0, fundedness_confidence))
        stability = max(0.0, min(1.0, sequence_stability))
        confidence = max(0.0, min(1.0, (sample_confidence * 0.45) + (fundedness * 0.30) + (stability * 0.25)))

        if confidence < 0.40:
            return None

        def _wmean(values: list[float], weight: float) -> float:
            return max(0.0, min(1.0, (sum(values) / max(1, len(values))) * weight))

        survivability = _wmean([s.execution_survivability_error for s in samples], 1.0)
        slippage = _wmean([s.slippage_underestimation for s in samples], 1.0)
        depth = _wmean([s.depth_overestimation for s in samples], 1.0)
        latency = _wmean([s.latency_miss_error for s in samples], 1.0)

        # Conservative only: recommendations only move toward stricter execution assumptions.
        queue_haircut_pct = max(0.15, min(0.95, 0.15 + (depth * 0.45) + (survivability * 0.20) + ((1.0 - fundedness) * 0.20)))
        drift_haircut_pct = max(0.10, min(0.95, 0.10 + (survivability * 0.45) + ((1.0 - stability) * 0.25)))
        latency_ms = int(max(120, min(12000, 120 + (latency * 6000) + ((1.0 - stability) * 2000))))
        snapshot_max_age_ms = int(max(300, min(2500, 1500 - (latency * 700) - ((1.0 - stability) * 300))))

        reasoning = (
            f"confidence={confidence:.3f}; samples={sample_count}; "
            f"fundedness={fundedness:.3f}; stability={stability:.3f}; "
            f"errors[survivability={survivability:.3f},slippage={slippage:.3f},depth={depth:.3f},latency={latency:.3f}]"
        )

        return CalibrationRecommendation(
            queue_haircut_pct=queue_haircut_pct,
            drift_haircut_pct=drift_haircut_pct,
            latency_ms=latency_ms,
            snapshot_max_age_ms=snapshot_max_age_ms,
            confidence_score=confidence,
            reasoning=reasoning,
        )
