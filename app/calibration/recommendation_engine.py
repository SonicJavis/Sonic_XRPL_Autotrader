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
    slippage_penalty_pct: float
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
        confidence_floor_threshold: float = 0.4,
        regime_transition_rate: float = 0.0,
        drift_error: float = 0.0,
        inclusion_uncertainty: float = 0.0,
        regime: str = "UNKNOWN",
        xrpl_risk_flags: dict[str, bool] | None = None,
        current_slippage_penalty_pct: float = 0.05,
        current_queue_haircut_pct: float = 0.15,
        current_drift_haircut_pct: float = 0.10,
        current_latency_ms: int = 120,
        current_snapshot_max_age_ms: int = 1500,
    ) -> CalibrationRecommendation | None:
        sample_count = len(samples)
        if sample_count < 5:
            return None

        sample_confidence = max(0.0, min(1.0, sample_count / 40.0))
        fundedness = max(0.0, min(1.0, fundedness_confidence))
        stability = max(0.0, min(1.0, sequence_stability))
        transition_penalty = max(0.0, min(1.0, regime_transition_rate))
        drift_penalty = max(0.0, min(1.0, drift_error))
        inclusion_penalty = max(0.0, min(1.0, inclusion_uncertainty))

        if regime == "SPOOFY":
            fundedness *= 0.70

        confidence = max(
            0.0,
            min(
                1.0,
                (sample_confidence * 0.35)
                + (fundedness * 0.25)
                + (stability * 0.20)
                + ((1.0 - transition_penalty) * 0.10)
                + ((1.0 - drift_penalty) * 0.05)
                + ((1.0 - inclusion_penalty) * 0.05),
            ),
        )

        if confidence < max(0.0, min(1.0, confidence_floor_threshold)):
            return None

        def _wmean(values: list[float], weight: float) -> float:
            return max(0.0, min(1.0, (sum(values) / max(1, len(values))) * weight))

        survivability = _wmean([s.execution_survivability_error for s in samples], 1.0)
        slippage = _wmean([s.slippage_underestimation for s in samples], 1.0)
        depth = _wmean([s.depth_overestimation for s in samples], 1.0)
        latency = _wmean([s.latency_miss_error for s in samples], 1.0)

        base_slippage_penalty_pct = max(0.05, min(0.95, 0.05 + (slippage * 0.55) + ((1.0 - stability) * 0.20)))
        base_queue_haircut_pct = max(0.15, min(0.95, 0.15 + (depth * 0.45) + (survivability * 0.20) + ((1.0 - fundedness) * 0.20)))
        base_drift_haircut_pct = max(0.10, min(0.95, 0.10 + (survivability * 0.45) + ((1.0 - stability) * 0.25)))
        base_latency_ms = int(max(120, min(12000, 120 + (latency * 6000) + ((1.0 - stability) * 2000))))
        base_snapshot_max_age_ms = int(max(300, min(2500, 1500 - (latency * 700) - ((1.0 - stability) * 300))))

        slippage_penalty_pct = base_slippage_penalty_pct
        queue_haircut_pct = base_queue_haircut_pct
        drift_haircut_pct = base_drift_haircut_pct
        latency_ms = base_latency_ms
        snapshot_max_age_ms = base_snapshot_max_age_ms

        if regime == "PATH_DISTORTED":
            slippage_penalty_pct = min(0.95, slippage_penalty_pct + 0.12)
        if regime == "ILLUSION_LIQUIDITY":
            queue_haircut_pct = min(0.95, queue_haircut_pct + 0.10)
        if regime == "COLLAPSING":
            drift_haircut_pct = min(0.95, drift_haircut_pct + 0.12)
            latency_ms = int(min(12000, latency_ms + 700))
            snapshot_max_age_ms = int(max(300, snapshot_max_age_ms - 150))

        flags = xrpl_risk_flags or {}
        if bool(flags.get("depth_illusion_risk")):
            queue_haircut_pct = min(0.95, queue_haircut_pct + 0.04)
        if bool(flags.get("pathfinding_risk")):
            slippage_penalty_pct = min(0.95, slippage_penalty_pct + 0.05)
        if bool(flags.get("inclusion_uncertainty")):
            latency_ms = int(min(12000, latency_ms + 250))
            snapshot_max_age_ms = int(max(300, snapshot_max_age_ms - 80))

        # Conservative only: outputs can never reduce existing penalties.
        slippage_penalty_pct = max(current_slippage_penalty_pct, slippage_penalty_pct)
        queue_haircut_pct = max(current_queue_haircut_pct, queue_haircut_pct)
        drift_haircut_pct = max(current_drift_haircut_pct, drift_haircut_pct)
        latency_ms = max(int(current_latency_ms), latency_ms)
        snapshot_max_age_ms = min(int(current_snapshot_max_age_ms), snapshot_max_age_ms)

        reasoning = (
            f"confidence={confidence:.3f}; samples={sample_count}; "
            f"fundedness={fundedness:.3f}; stability={stability:.3f}; regime={regime}; "
            f"errors[survivability={survivability:.3f},slippage={slippage:.3f},depth={depth:.3f},latency={latency:.3f}]"
        )

        return CalibrationRecommendation(
            slippage_penalty_pct=slippage_penalty_pct,
            queue_haircut_pct=queue_haircut_pct,
            drift_haircut_pct=drift_haircut_pct,
            latency_ms=latency_ms,
            snapshot_max_age_ms=snapshot_max_age_ms,
            confidence_score=confidence,
            reasoning=reasoning,
        )
