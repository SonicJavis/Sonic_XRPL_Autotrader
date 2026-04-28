from __future__ import annotations

from dataclasses import dataclass
from math import exp

from app.db.models import ExecutionRecord


def _clamp_unit(raw: float) -> float:
    return max(0.0, min(1.0, float(raw)))


@dataclass(slots=True)
class XRPLTimeExecutionInput:
    snapshot_price: float
    execution_price: float
    requested_size: float
    snapshot_derived_liquidity: float
    observed_possible_fill: float
    ledger_index_snapshot: int
    ledger_index_execution: int
    competition_penalty: float
    base_fill_probability: float
    path_complexity: int
    slippage_estimate: float


@dataclass(slots=True)
class XRPLTimeExecutionResult:
    latency_seconds: float
    ledger_delay: int
    price_drift: float
    drift_amplified: float
    liquidity_decay: float
    time_adjusted_phantom: float
    inclusion_probability: float
    effective_fill_probability: float
    drift_adjusted_ev: float


class XRPLTimeExecutionModel:
    """Deterministic advisory model for ledger-timed XRPL shadow execution."""

    def evaluate(self, data: XRPLTimeExecutionInput) -> XRPLTimeExecutionResult:
        snapshot_price = float(data.snapshot_price)
        execution_price = float(data.execution_price)
        snapshot_derived_liquidity = max(0.0, float(data.snapshot_derived_liquidity))
        observed_possible_fill = max(0.0, float(data.observed_possible_fill))
        ledger_delay = max(0, int(data.ledger_index_execution) - int(data.ledger_index_snapshot))
        latency_seconds = float(ledger_delay * 4)

        price_ref = max(abs(snapshot_price), 1e-9)
        price_drift = (execution_price - snapshot_price) / price_ref
        liquidity_decay = min(observed_possible_fill / max(snapshot_derived_liquidity, 1e-9), 1.0)
        phantom_liquidity = max(snapshot_derived_liquidity - observed_possible_fill, 0.0)
        time_adjusted_phantom = phantom_liquidity * (1.0 + latency_seconds / 10.0)
        latency_penalty = min(latency_seconds / 20.0, 1.0)
        path_penalty = min(max(0, int(data.path_complexity)) / 3.0, 1.0)
        inclusion_probability = exp(-ledger_delay / 3.0)
        competition_penalty = _clamp_unit(data.competition_penalty)
        base_fill_probability = _clamp_unit(data.base_fill_probability)
        slippage_estimate = max(0.0, float(data.slippage_estimate))

        effective_fill_probability = _clamp_unit(
            base_fill_probability
            * liquidity_decay
            * (1.0 - competition_penalty)
            * (1.0 - path_penalty)
            * inclusion_probability
            * (1.0 - latency_penalty)
        )
        drift_amplified = abs(price_drift) * (1.0 + path_penalty + latency_penalty)
        drift_adjusted_ev = (
            effective_fill_probability
            * (1.0 - drift_amplified - slippage_estimate)
            - (1.0 - effective_fill_probability)
        )

        return XRPLTimeExecutionResult(
            latency_seconds=round(latency_seconds, 6),
            ledger_delay=ledger_delay,
            price_drift=round(price_drift, 6),
            drift_amplified=round(drift_amplified, 6),
            liquidity_decay=round(liquidity_decay, 6),
            time_adjusted_phantom=round(time_adjusted_phantom, 6),
            inclusion_probability=round(inclusion_probability, 6),
            effective_fill_probability=round(effective_fill_probability, 6),
            drift_adjusted_ev=round(drift_adjusted_ev, 6),
        )


def build_time_execution_input_from_shadow_execution(execution: ExecutionRecord, details: dict[str, object]) -> XRPLTimeExecutionInput:
    requested_size = max(0.0, float(execution.requested_size or 0.0))
    filled_size = max(0.0, float(execution.filled_size or 0.0))
    simulated_fill_ratio = 0.0 if requested_size <= 0 else _clamp_unit(filled_size / requested_size)
    snapshot_price = max(0.0, float(details.get("snapshot_price", execution.avg_fill_price or 0.0)))
    execution_price = max(0.0, float(details.get("execution_price", execution.avg_fill_price or snapshot_price)))
    observed_possible_fill = max(
        0.0,
        float(details.get("observed_possible_fill", _clamp_unit(float(details.get("observed_fill_ratio", simulated_fill_ratio))) * requested_size)),
    )
    snapshot_derived_liquidity = max(
        0.0,
        float(details.get("snapshot_derived_liquidity", max(requested_size, observed_possible_fill))),
    )
    routes_seen = details.get("routes_seen", [])
    if isinstance(routes_seen, list) and routes_seen:
        fallback_path_complexity = len({str(route) for route in routes_seen})
    else:
        fallback_path_complexity = int(details.get("route_count", 1))
    return XRPLTimeExecutionInput(
        snapshot_price=snapshot_price,
        execution_price=execution_price,
        requested_size=requested_size,
        snapshot_derived_liquidity=snapshot_derived_liquidity,
        observed_possible_fill=observed_possible_fill,
        ledger_index_snapshot=int(execution.ledger_index_snapshot or 0),
        ledger_index_execution=int(execution.ledger_index_execution or execution.ledger_index_inclusion or 0),
        competition_penalty=_clamp_unit(float(details.get("competition_penalty", 0.0))),
        base_fill_probability=_clamp_unit(float(details.get("predicted_fill_probability", simulated_fill_ratio))),
        path_complexity=max(0, int(details.get("path_complexity", fallback_path_complexity))),
        slippage_estimate=max(0.0, float(details.get("slippage_estimate", abs(float(execution.slippage_vs_top or 0.0))))),
    )
