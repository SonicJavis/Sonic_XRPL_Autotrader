from __future__ import annotations

from dataclasses import dataclass

from app.calibration.snapshot_flags import build_xrpl_risk_flags


@dataclass(slots=True)
class RegimeClassificationInput:
    visible_depth_score: float
    execution_survivability_error: float
    slippage_underestimation: float
    depth_overestimation: float
    volatility_score: float
    decay_score: float
    wall_flicker_rate: float
    inclusion_uncertainty: float


@dataclass(slots=True)
class RegimeClassificationResult:
    regime: str
    confidence: float
    xrpl_flags: dict[str, bool]


class XRPLRegimeClassifier:
    def classify(
        self,
        *,
        metrics: RegimeClassificationInput,
        confidence_floor_threshold: float = 0.4,
    ) -> RegimeClassificationResult:
        depth = max(0.0, min(1.0, metrics.visible_depth_score))
        survivability_error = max(0.0, min(1.0, metrics.execution_survivability_error))
        slippage = max(0.0, min(1.0, metrics.slippage_underestimation))
        depth_over = max(0.0, min(1.0, metrics.depth_overestimation))
        volatility = max(0.0, min(1.0, metrics.volatility_score))
        decay = max(0.0, min(1.0, metrics.decay_score))
        flicker = max(0.0, min(1.0, metrics.wall_flicker_rate))
        inclusion_uncertainty = max(0.0, min(1.0, metrics.inclusion_uncertainty))

        regime = "UNKNOWN"
        if depth >= 0.7 and survivability_error >= 0.5:
            regime = "ILLUSION_LIQUIDITY"
        elif volatility <= 0.35 and slippage >= 0.45:
            regime = "PATH_DISTORTED"
        elif decay >= 0.75:
            regime = "COLLAPSING"
        elif flicker >= 0.6:
            regime = "SPOOFY"
        elif volatility >= 0.75:
            regime = "HIGH_VOLATILITY"
        elif depth <= 0.25:
            regime = "THIN"
        elif volatility <= 0.25 and decay <= 0.25 and flicker <= 0.20:
            regime = "STABLE"

        confidence = max(
            0.0,
            min(
                1.0,
                1.0
                - (
                    (inclusion_uncertainty * 0.35)
                    + (volatility * 0.20)
                    + (flicker * 0.20)
                    + (abs(survivability_error - depth_over) * 0.25)
                ),
            ),
        )

        xrpl_flags = build_xrpl_risk_flags(
            confidence_score=confidence,
            confidence_floor_threshold=confidence_floor_threshold,
            possible_unfunded_liquidity=(regime in {"ILLUSION_LIQUIDITY", "SPOOFY", "THIN", "UNKNOWN"}),
            pathfinding_risk=(regime in {"PATH_DISTORTED", "HIGH_VOLATILITY", "UNKNOWN"}),
            inclusion_uncertainty=(inclusion_uncertainty >= 0.4 or regime in {"COLLAPSING", "UNKNOWN"}),
            depth_illusion_risk=(regime in {"ILLUSION_LIQUIDITY", "PATH_DISTORTED", "UNKNOWN"}),
        )

        return RegimeClassificationResult(regime=regime, confidence=confidence, xrpl_flags=xrpl_flags)
