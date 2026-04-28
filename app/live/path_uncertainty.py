from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PathUncertaintyInput:
    direct_book_depth_xrp: float
    autobridged_book_depth_xrp: float
    route_count: int
    top_of_book_churn: float
    snapshot_age_ms: int
    ledger_delay_error: float
    missing_ledger_ratio: float


@dataclass(slots=True)
class PathUncertainty:
    multi_hop_risk: float
    route_instability: float
    path_distortion_likelihood: float
    path_execution_risk: float
    route_confidence: float


class PathUncertaintyModel:
    def evaluate(self, data: PathUncertaintyInput) -> PathUncertainty:
        direct_depth = max(0.0, float(data.direct_book_depth_xrp))
        autobridged_depth = max(0.0, float(data.autobridged_book_depth_xrp))
        route_count = max(0, int(data.route_count))
        churn = max(0.0, min(1.0, float(data.top_of_book_churn)))
        age_penalty = max(0.0, min(1.0, float(data.snapshot_age_ms) / 5000.0))
        ledger_delay = max(0.0, min(1.0, float(data.ledger_delay_error)))
        missing_ratio = max(0.0, min(1.0, float(data.missing_ledger_ratio)))

        multi_hop_risk = max(0.0, min(1.0, 0.15 + (0.18 * max(0, route_count - 1)) + (0.25 if direct_depth <= 0 else 0.0)))

        depth_ratio = 0.0
        if autobridged_depth > 0:
            depth_ratio = direct_depth / autobridged_depth
        path_distortion_likelihood = max(
            0.0,
            min(
                1.0,
                (0.45 * max(0.0, 1.0 - min(1.0, depth_ratio)))
                + (0.20 * multi_hop_risk)
                + (0.20 * churn)
                + (0.15 * ledger_delay),
            ),
        )

        route_instability = max(
            0.0,
            min(
                1.0,
                (0.35 * churn)
                + (0.20 * age_penalty)
                + (0.20 * ledger_delay)
                + (0.25 * missing_ratio),
            ),
        )

        path_execution_risk = max(
            0.0,
            min(1.0, (0.35 * multi_hop_risk) + (0.30 * route_instability) + (0.35 * path_distortion_likelihood)),
        )
        route_confidence = max(0.0, min(1.0, 1.0 - path_execution_risk))

        return PathUncertainty(
            multi_hop_risk=round(multi_hop_risk, 6),
            route_instability=round(route_instability, 6),
            path_distortion_likelihood=round(path_distortion_likelihood, 6),
            path_execution_risk=round(path_execution_risk, 6),
            route_confidence=round(route_confidence, 6),
        )