from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from math import isfinite

from app.calibration.xrpl_time_execution_model import XRPLTimeExecutionModel, build_time_execution_input_from_shadow_execution
from app.db.models import ExecutionRecord, WatchedToken


def _finite_float(raw: object, *, default: float = 0.0) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return default
    return value if isfinite(value) else default


def _finite_int(raw: object, *, default: int = 0) -> int:
    try:
        return int(_finite_float(raw, default=float(default)))
    except (TypeError, ValueError, OverflowError):
        return default


def _clamp_unit(raw: object) -> float:
    return max(0.0, min(1.0, _finite_float(raw)))


def _utc(ts: datetime) -> datetime:
    if ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def _details(row: ExecutionRecord) -> dict[str, object]:
    try:
        payload = json.loads(str(row.execution_details_json or "{}"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


@dataclass(slots=True)
class XRPLMemorySample:
    token_id: int
    issuer: str
    currency: str
    phantom_liquidity: float
    phantom_penalty: float
    observed_possible_fill: float
    snapshot_derived_liquidity: float
    route_instability: float
    path_complexity: int
    routes_seen_count: int
    ledger_delay: int
    latency_seconds: float
    competition_penalty: float
    low_fill_bias: float
    drift: float
    drift_adjusted_ev: float
    effective_fill_probability: float
    observed_at: datetime

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["observed_at"] = _utc(self.observed_at).isoformat()
        return data


@dataclass(slots=True)
class XRPLMemoryAggregate:
    scope: str
    key: str
    sample_count: int
    avg_phantom_penalty: float
    avg_liquidity_decay: float
    avg_route_instability: float
    avg_path_complexity: float
    avg_latency_seconds: float
    avg_competition_penalty: float
    avg_low_fill_bias: float
    avg_drift: float
    avg_drift_adjusted_ev: float
    avg_effective_fill_probability: float
    liquidity_reliability: float
    execution_reliability: float
    regime_pressure_score: float
    advisory_risk_level: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _risk_level(score: float) -> str:
    score = _clamp_unit(score)
    if score >= 0.85:
        return "CRITICAL"
    if score >= 0.60:
        return "HIGH"
    if score >= 0.30:
        return "MEDIUM"
    return "LOW"


def _aggregate(scope: str, key: str, samples: list[XRPLMemorySample]) -> XRPLMemoryAggregate:
    if not samples:
        return XRPLMemoryAggregate(
            scope=scope,
            key=key,
            sample_count=0,
            avg_phantom_penalty=0.0,
            avg_liquidity_decay=0.0,
            avg_route_instability=0.0,
            avg_path_complexity=0.0,
            avg_latency_seconds=0.0,
            avg_competition_penalty=0.0,
            avg_low_fill_bias=0.0,
            avg_drift=0.0,
            avg_drift_adjusted_ev=0.0,
            avg_effective_fill_probability=0.0,
            liquidity_reliability=0.0,
            execution_reliability=0.0,
            regime_pressure_score=1.0,
            advisory_risk_level="CRITICAL",
        )

    count = len(samples)

    def avg(values: list[float]) -> float:
        clean = [value for value in values if isfinite(value)]
        return 0.0 if not clean else round(sum(clean) / len(clean), 6)

    avg_phantom_penalty = avg([row.phantom_penalty for row in samples])
    avg_liquidity_decay = avg(
        [
            0.0
            if row.snapshot_derived_liquidity <= 0.0
            else min(row.observed_possible_fill / max(row.snapshot_derived_liquidity, 1e-9), 1.0)
            for row in samples
        ]
    )
    avg_route_instability = avg([row.route_instability for row in samples])
    avg_path_complexity = avg([float(row.path_complexity) for row in samples])
    avg_latency_seconds = avg([row.latency_seconds for row in samples])
    avg_competition_penalty = avg([row.competition_penalty for row in samples])
    avg_low_fill_bias = avg([row.low_fill_bias for row in samples])
    avg_drift = avg([row.drift for row in samples])
    avg_drift_adjusted_ev = avg([row.drift_adjusted_ev for row in samples])
    avg_effective_fill_probability = avg([row.effective_fill_probability for row in samples])

    liquidity_reliability = round(_clamp_unit(avg_liquidity_decay * (1.0 - avg_phantom_penalty)), 6)
    execution_reliability = round(
        _clamp_unit(avg_effective_fill_probability * (1.0 - avg_low_fill_bias) * (1.0 - avg_competition_penalty)),
        6,
    )
    latency_pressure = _clamp_unit(avg_latency_seconds / 20.0)
    path_pressure = _clamp_unit(avg_path_complexity / 3.0)
    drift_pressure = _clamp_unit(abs(avg_drift) + max(0.0, -avg_drift_adjusted_ev))
    regime_pressure_score = round(
        _clamp_unit(
            (1.0 - liquidity_reliability) * 0.25
            + (1.0 - execution_reliability) * 0.30
            + avg_route_instability * 0.15
            + avg_competition_penalty * 0.10
            + latency_pressure * 0.10
            + max(path_pressure, drift_pressure) * 0.10
        ),
        6,
    )
    return XRPLMemoryAggregate(
        scope=scope,
        key=key,
        sample_count=count,
        avg_phantom_penalty=avg_phantom_penalty,
        avg_liquidity_decay=avg_liquidity_decay,
        avg_route_instability=avg_route_instability,
        avg_path_complexity=avg_path_complexity,
        avg_latency_seconds=avg_latency_seconds,
        avg_competition_penalty=avg_competition_penalty,
        avg_low_fill_bias=avg_low_fill_bias,
        avg_drift=avg_drift,
        avg_drift_adjusted_ev=avg_drift_adjusted_ev,
        avg_effective_fill_probability=avg_effective_fill_probability,
        liquidity_reliability=liquidity_reliability,
        execution_reliability=execution_reliability,
        regime_pressure_score=regime_pressure_score,
        advisory_risk_level=_risk_level(regime_pressure_score),
    )


def build_memory_samples(
    executions: list[ExecutionRecord],
    *,
    tokens_by_id: dict[int, WatchedToken] | None = None,
) -> list[XRPLMemorySample]:
    samples: list[XRPLMemorySample] = []
    model = XRPLTimeExecutionModel()
    for row in executions:
        details = _details(row)
        if not bool(details.get("shadow")):
            continue
        token_id = _finite_int(row.token_id)
        token = (tokens_by_id or {}).get(token_id)
        issuer = str(details.get("issuer") or (token.issuer if token is not None else f"token:{token_id}"))
        currency = str(details.get("currency") or (token.currency if token is not None else "UNKNOWN"))
        data = build_time_execution_input_from_shadow_execution(row, details)
        result = model.evaluate(data)
        routes_seen = details.get("routes_seen", [])
        routes_seen_count = len({str(route) for route in routes_seen}) if isinstance(routes_seen, list) else 0
        phantom_liquidity = max(data.snapshot_derived_liquidity - data.observed_possible_fill, 0.0)
        phantom_penalty = 0.0
        if data.requested_size > 0.0:
            phantom_penalty = _clamp_unit(phantom_liquidity / data.requested_size)
        simulated_fill_ratio = 0.0 if data.requested_size <= 0.0 else _clamp_unit(_finite_float(row.filled_size) / data.requested_size)
        observed_fill_ratio = 0.0 if data.requested_size <= 0.0 else _clamp_unit(data.observed_possible_fill / data.requested_size)
        low_fill_bias = _clamp_unit(max(0.0, simulated_fill_ratio - observed_fill_ratio))
        samples.append(
            XRPLMemorySample(
                token_id=token_id,
                issuer=issuer,
                currency=currency,
                phantom_liquidity=round(phantom_liquidity, 6),
                phantom_penalty=round(phantom_penalty, 6),
                observed_possible_fill=round(data.observed_possible_fill, 6),
                snapshot_derived_liquidity=round(data.snapshot_derived_liquidity, 6),
                route_instability=_clamp_unit(details.get("route_instability", details.get("path_execution_risk", 0.0))),
                path_complexity=max(0, int(data.path_complexity)),
                routes_seen_count=routes_seen_count,
                ledger_delay=result.ledger_delay,
                latency_seconds=result.latency_seconds,
                competition_penalty=_clamp_unit(details.get("competition_penalty", 1.0 if low_fill_bias >= 0.30 else 0.0)),
                low_fill_bias=round(low_fill_bias, 6),
                drift=result.price_drift,
                drift_adjusted_ev=result.drift_adjusted_ev,
                effective_fill_probability=result.effective_fill_probability,
                observed_at=_utc(row.execution_time),
            )
        )
    return sorted(samples, key=lambda sample: (sample.token_id, sample.issuer, sample.currency, sample.observed_at.isoformat()))


def aggregate_global(samples: list[XRPLMemorySample]) -> XRPLMemoryAggregate:
    return _aggregate("global", "all", samples)


def aggregate_by_token(samples: list[XRPLMemorySample]) -> list[XRPLMemoryAggregate]:
    grouped: dict[str, list[XRPLMemorySample]] = {}
    for sample in samples:
        grouped.setdefault(str(sample.token_id), []).append(sample)
    return [_aggregate("token", key, grouped[key]) for key in sorted(grouped, key=lambda value: int(value))]


def aggregate_by_issuer(samples: list[XRPLMemorySample]) -> list[XRPLMemoryAggregate]:
    grouped: dict[str, list[XRPLMemorySample]] = {}
    for sample in samples:
        grouped.setdefault(sample.issuer, []).append(sample)
    return [_aggregate("issuer", key, grouped[key]) for key in sorted(grouped)]
