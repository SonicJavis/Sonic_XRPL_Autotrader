from __future__ import annotations

from dataclasses import asdict, dataclass

from app.calibration.xrpl_memory_model import XRPLMemoryAggregate


def _clamp_unit(raw: float) -> float:
    return max(0.0, min(1.0, float(raw)))


@dataclass(slots=True)
class XRPLRegimeAssessment:
    regime: str
    severity_score: float
    risk_flags: list[str]
    advisory_only: bool
    is_shadow: bool
    is_executable: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class XRPLRegimeDetector:
    def assess(self, aggregate: XRPLMemoryAggregate) -> XRPLRegimeAssessment:
        flags: list[str] = []
        severity = 0.0
        regime = "STABLE_SHADOW"

        liquidity_illusion = aggregate.avg_phantom_penalty >= 0.45 and aggregate.avg_liquidity_decay <= 0.35
        route_unstable = aggregate.avg_route_instability >= 0.45 or aggregate.avg_path_complexity >= 2.0
        path_failure_risk = aggregate.avg_path_complexity >= 3.0 and aggregate.avg_route_instability >= 0.5
        liquidity_fragmentation = aggregate.avg_routes_seen_count >= 3.0 and aggregate.avg_low_fill_bias >= 0.25
        issuer_risk_proxy = abs(aggregate.avg_drift) >= 0.08 and aggregate.execution_reliability <= 0.35
        competition_spike = aggregate.avg_competition_penalty >= 0.45 and aggregate.avg_low_fill_bias >= 0.25
        latency_dominated = aggregate.avg_latency_seconds >= 12.0
        drift_risk = aggregate.avg_drift_adjusted_ev < 0.0 and abs(aggregate.avg_drift) >= 0.05
        execution_collapse = aggregate.avg_effective_fill_probability <= 0.10

        if liquidity_illusion:
            flags.append("PHANTOM_LIQUIDITY_PERSISTENT")
        if route_unstable:
            flags.append("PATHFINDING_UNSTABLE")
        if path_failure_risk:
            flags.append("PATH_FAILURE_RISK")
            flags.append("ROUTING_INSTABILITY_CLUSTER")
        if liquidity_fragmentation:
            flags.append("LIQUIDITY_FRAGMENTATION")
        if issuer_risk_proxy:
            flags.append("ISSUER_RISK_PROXY")
        if competition_spike:
            flags.append("INVISIBLE_COMPETITION_SPIKE")
        if latency_dominated:
            flags.append("LEDGER_LATENCY_DOMINATED")
        if drift_risk:
            flags.append("ADVERSARIAL_PRICE_DRIFT")
        if execution_collapse:
            flags.append("EXECUTION_PROBABILITY_COLLAPSE")

        if execution_collapse:
            regime = "EXECUTION_COLLAPSE"
            severity = 1.0
        elif liquidity_illusion:
            regime = "LIQUIDITY_ILLUSION"
            severity = max(severity, 0.85)
        elif path_failure_risk:
            regime = "ROUTE_UNSTABLE"
            severity = max(severity, 0.82)
        elif competition_spike:
            regime = "COMPETITION_SPIKE"
            severity = max(severity, 0.80)
        elif latency_dominated:
            regime = "LATENCY_DOMINATED"
            severity = max(severity, 0.72)
        elif drift_risk:
            regime = "DRIFT_RISK"
            severity = max(severity, 0.70)
        elif route_unstable:
            regime = "ROUTE_UNSTABLE"
            severity = max(severity, 0.65)
        else:
            severity = max(0.0, min(0.25, aggregate.regime_pressure_score))

        worst_case_amplification = max(
            aggregate.regime_pressure_score,
            aggregate.avg_phantom_penalty,
            aggregate.avg_route_instability,
            aggregate.avg_competition_penalty,
            min(1.0, aggregate.avg_latency_seconds / 20.0),
            min(1.0, aggregate.avg_path_complexity / 3.0),
            min(1.0, abs(aggregate.avg_drift) * (1.0 + aggregate.avg_latency_seconds / 10.0)),
            1.0 - aggregate.execution_reliability,
        )
        severity = max(severity, worst_case_amplification)
        return XRPLRegimeAssessment(
            regime=regime,
            severity_score=round(_clamp_unit(severity), 6),
            risk_flags=flags,
            advisory_only=True,
            is_shadow=True,
            is_executable=False,
        )
