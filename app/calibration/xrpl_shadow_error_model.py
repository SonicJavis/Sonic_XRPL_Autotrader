from __future__ import annotations

from dataclasses import dataclass


def _clamp_unit(raw: float) -> float:
    return max(0.0, min(1.0, float(raw)))


@dataclass(slots=True)
class XRPLShadowErrorInput:
    requested_size: float
    simulated_fill_ratio: float
    observed_fill_ratio: float
    snapshot_derived_liquidity: float
    observed_possible_fill: float
    price_error_norm: float
    liquidity_error: float
    ledger_delay_error: float
    path_error: float
    observation_confidence: float
    route_confidence: float
    unique_routes_seen: int = 0
    total_snapshots: int = 0


@dataclass(slots=True)
class XRPLShadowErrorMetrics:
    phantom_liquidity: float
    phantom_penalty: float
    route_instability: float
    competition_penalty: float
    fill_variance: float
    low_fill_bias: float
    fill_disagreement: float
    raw_error: float
    weighted_error: float


class XRPLShadowErrorModel:
    """XRPL-aware pessimistic shadow disagreement model."""

    def evaluate(self, data: XRPLShadowErrorInput) -> XRPLShadowErrorMetrics:
        requested_size = max(1e-9, float(data.requested_size))
        simulated_fill_ratio = _clamp_unit(float(data.simulated_fill_ratio))
        observed_fill_ratio = _clamp_unit(float(data.observed_fill_ratio))
        snapshot_derived_liquidity = max(0.0, float(data.snapshot_derived_liquidity))
        observed_possible_fill = max(0.0, float(data.observed_possible_fill))
        price_error_norm = _clamp_unit(float(data.price_error_norm))
        liquidity_error = _clamp_unit(float(data.liquidity_error))
        ledger_delay_error = _clamp_unit(float(data.ledger_delay_error))
        path_error = _clamp_unit(float(data.path_error))
        observation_confidence = _clamp_unit(float(data.observation_confidence))
        route_confidence = _clamp_unit(float(data.route_confidence))
        unique_routes_seen = max(0, int(data.unique_routes_seen))
        total_snapshots = max(0, int(data.total_snapshots))

        phantom_liquidity = max(0.0, snapshot_derived_liquidity - observed_possible_fill)
        phantom_penalty = _clamp_unit(phantom_liquidity / requested_size)

        if total_snapshots > 0 and unique_routes_seen > 1:
            route_instability = _clamp_unit(unique_routes_seen / float(total_snapshots))
        else:
            route_instability = _clamp_unit(1.0 - route_confidence)

        competition_penalty = 1.0 if simulated_fill_ratio > 0.5 and observed_fill_ratio < 0.2 else 0.0

        fill_variance = _clamp_unit(abs(simulated_fill_ratio - observed_fill_ratio))
        low_fill_bias = _clamp_unit(max(0.0, simulated_fill_ratio - observed_fill_ratio))
        fill_disagreement = _clamp_unit((fill_variance * 0.65) + (low_fill_bias * 0.35))

        raw_error = _clamp_unit(
            (0.25 * fill_disagreement)
            + (0.15 * price_error_norm)
            + (0.15 * liquidity_error)
            + (0.10 * ledger_delay_error)
            + (0.10 * path_error)
            + (0.10 * phantom_penalty)
            + (0.10 * route_instability)
            + (0.05 * competition_penalty)
        )
        weighted_error = _clamp_unit(raw_error * (1.0 + (1.0 - observation_confidence)))

        return XRPLShadowErrorMetrics(
            phantom_liquidity=round(phantom_liquidity, 6),
            phantom_penalty=round(phantom_penalty, 6),
            route_instability=round(route_instability, 6),
            competition_penalty=round(competition_penalty, 6),
            fill_variance=round(fill_variance, 6),
            low_fill_bias=round(low_fill_bias, 6),
            fill_disagreement=round(fill_disagreement, 6),
            raw_error=round(raw_error, 6),
            weighted_error=round(weighted_error, 6),
        )