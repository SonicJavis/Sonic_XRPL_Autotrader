from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any


RISK_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


def _finite_float(raw: object, *, default: float = 0.0) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return default
    return value if isfinite(value) else default


def _clamp_unit(raw: object) -> float:
    return max(0.0, min(1.0, _finite_float(raw)))


def _read(source: object | None, name: str, default: object = 0.0) -> object:
    if source is None:
        return default
    if isinstance(source, dict):
        return source.get(name, default)
    return getattr(source, name, default)


def _as_dict(source: object | None) -> dict[str, object]:
    if source is None:
        return {}
    if isinstance(source, dict):
        return dict(source)
    if hasattr(source, "to_dict"):
        return dict(source.to_dict())
    if hasattr(source, "__dataclass_fields__"):
        return asdict(source)
    return {}


def _risk_level(source: object | None) -> str:
    value = str(_read(source, "advisory_risk_level", "LOW")).upper()
    return value if value in RISK_ORDER else "LOW"


def _worst_risk_level(levels: list[str]) -> str:
    return max(levels, key=lambda level: RISK_ORDER.get(level, 0), default="LOW")


def _regime_name(source: object | None) -> str:
    return str(_read(source, "regime", "STABLE_SHADOW")).upper()


def _regime_flags(source: object | None) -> list[str]:
    flags = _read(source, "risk_flags", [])
    if not isinstance(flags, list):
        return []
    return sorted({str(flag).upper() for flag in flags})


@dataclass(slots=True)
class XRPLMemoryWeightingInput:
    global_aggregate: object | None
    token_aggregate: object | None
    issuer_aggregate: object | None
    global_regime: object | None
    token_regime: object | None
    issuer_regime: object | None


@dataclass(slots=True)
class XRPLMemoryWeightingResult:
    execution_probability_multiplier: float
    effective_size_multiplier: float
    slippage_multiplier_boost: float
    ev_penalty: float
    risk_flags: list[str]
    advisory_risk_level: str
    reasoning: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class XRPLMemoryWeighting:
    def evaluate(self, data: XRPLMemoryWeightingInput) -> XRPLMemoryWeightingResult:
        aggregates = [row for row in (data.global_aggregate, data.token_aggregate, data.issuer_aggregate) if row is not None]
        regimes = [row for row in (data.global_regime, data.token_regime, data.issuer_regime) if row is not None]

        probability_multiplier = 1.0
        size_multiplier = 1.0
        slippage_boost = 1.0
        ev_penalty = 0.0
        risk_flags: set[str] = set()
        reasoning: list[str] = []

        advisory_risk_level = _worst_risk_level([_risk_level(row) for row in aggregates])
        risk_reductions = {
            "LOW": (1.0, 1.0),
            "MEDIUM": (0.88, 0.90),
            "HIGH": (0.70, 0.72),
            "CRITICAL": (0.40, 0.45),
        }
        risk_probability, risk_size = risk_reductions[advisory_risk_level]
        probability_multiplier *= risk_probability
        size_multiplier *= risk_size
        if advisory_risk_level != "LOW":
            reasoning.append(f"{advisory_risk_level} memory risk reduced advisory exposure")

        for aggregate in aggregates:
            label = str(_read(aggregate, "scope", "memory"))
            pressure = _clamp_unit(_read(aggregate, "regime_pressure_score", 0.0))
            liquidity_reliability = _clamp_unit(_read(aggregate, "liquidity_reliability", 1.0))
            execution_reliability = _clamp_unit(_read(aggregate, "execution_reliability", 1.0))
            phantom_penalty = _clamp_unit(_read(aggregate, "avg_phantom_penalty", 0.0))
            route_instability = _clamp_unit(_read(aggregate, "avg_route_instability", 0.0))
            latency_seconds = max(0.0, _finite_float(_read(aggregate, "avg_latency_seconds", 0.0)))
            drift_adjusted_ev = _finite_float(_read(aggregate, "avg_drift_adjusted_ev", 0.0))

            probability_multiplier *= 1.0 - (0.35 * pressure)
            probability_multiplier *= 0.55 + (0.45 * execution_reliability)
            size_multiplier *= 0.50 + (0.50 * liquidity_reliability)
            size_multiplier *= 1.0 - (0.40 * phantom_penalty)
            slippage_boost *= 1.0 + (0.50 * route_instability)
            ev_penalty += min(latency_seconds / 120.0, 0.25)
            if drift_adjusted_ev < 0.0:
                ev_penalty += min(abs(drift_adjusted_ev), 1.0)

            if pressure > 0.0:
                reasoning.append(f"{label} regime pressure {pressure:.3f} reduced probability")
            if liquidity_reliability < 0.5:
                reasoning.append(f"{label} liquidity reliability is weak")
            if execution_reliability < 0.5:
                reasoning.append(f"{label} execution reliability is weak")

        regime_flag_map = {
            "LIQUIDITY_ILLUSION": "PHANTOM_LIQUIDITY_MEMORY",
            "ROUTE_UNSTABLE": "ROUTE_MEMORY_UNSTABLE",
            "COMPETITION_SPIKE": "COMPETITION_MEMORY_SPIKE",
            "LATENCY_DOMINATED": "LATENCY_MEMORY_DOMINATED",
            "DRIFT_RISK": "DRIFT_MEMORY_RISK",
            "EXECUTION_COLLAPSE": "EXECUTION_MEMORY_COLLAPSE",
        }
        signal_flag_map = {
            "PATH_FAILURE_RISK": "PATH_MEMORY_FAILURE",
            "ISSUER_RISK_PROXY": "ISSUER_MEMORY_RISK",
            "LIQUIDITY_FRAGMENTATION": "LIQUIDITY_MEMORY_FRAGMENTED",
        }

        for regime in regimes:
            regime_name = _regime_name(regime)
            mapped = regime_flag_map.get(regime_name)
            if mapped:
                risk_flags.add(mapped)
                reasoning.append(f"{regime_name} memory regime applied")
            severity = _clamp_unit(_read(regime, "severity_score", 0.0))
            probability_multiplier *= 1.0 - (0.30 * severity)
            for source_flag in _regime_flags(regime):
                mapped_flag = signal_flag_map.get(source_flag)
                if mapped_flag:
                    risk_flags.add(mapped_flag)

        if "EXECUTION_MEMORY_COLLAPSE" in risk_flags:
            probability_multiplier = min(probability_multiplier, 0.10)
            size_multiplier = min(size_multiplier, 0.10)
            ev_penalty += 1.0

        return XRPLMemoryWeightingResult(
            execution_probability_multiplier=round(_clamp_unit(probability_multiplier), 6),
            effective_size_multiplier=round(_clamp_unit(size_multiplier), 6),
            slippage_multiplier_boost=round(max(1.0, _finite_float(slippage_boost, default=1.0)), 6),
            ev_penalty=round(max(0.0, _finite_float(ev_penalty)), 6),
            risk_flags=sorted(risk_flags),
            advisory_risk_level=advisory_risk_level,
            reasoning=reasoning or ["No memory weighting applied"],
        )


def build_memory_weighting_from_payload(memory: dict[str, Any] | None) -> XRPLMemoryWeightingResult:
    payload = _as_dict(memory)
    return XRPLMemoryWeighting().evaluate(
        XRPLMemoryWeightingInput(
            global_aggregate=payload.get("global"),
            token_aggregate=payload.get("token"),
            issuer_aggregate=payload.get("issuer"),
            global_regime=payload.get("global_regime"),
            token_regime=payload.get("token_regime"),
            issuer_regime=payload.get("issuer_regime"),
        )
    )
