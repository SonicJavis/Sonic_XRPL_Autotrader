from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from math import isfinite

from app.db.models import ShadowDecisionRecord


def _finite_float(raw: object, *, default: float = 0.0) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return default
    return value if isfinite(value) else default


def _flags(row: ShadowDecisionRecord) -> list[str]:
    try:
        payload = json.loads(str(row.risk_flags_json or "[]"))
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    return sorted({str(flag) for flag in payload})


@dataclass(slots=True)
class ShadowDecisionSummary:
    sample_count: int
    avg_memory_adjusted_probability: float
    avg_effective_size: float
    avg_adjusted_ev: float
    avg_drift_adjusted_ev: float
    over_risk_rate: float
    blocked_rate: float
    regime_distribution: dict[str, int]
    risk_flag_counts: dict[str, int]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class ShadowDecisionTracker:
    def summarize(self, rows: list[ShadowDecisionRecord]) -> ShadowDecisionSummary:
        if not rows:
            return ShadowDecisionSummary(
                sample_count=0,
                avg_memory_adjusted_probability=0.0,
                avg_effective_size=0.0,
                avg_adjusted_ev=0.0,
                avg_drift_adjusted_ev=0.0,
                over_risk_rate=0.0,
                blocked_rate=0.0,
                regime_distribution={},
                risk_flag_counts={},
            )

        count = len(rows)
        regime_distribution: dict[str, int] = {}
        risk_flag_counts: dict[str, int] = {}
        blocked = 0
        over_risk = 0
        for row in rows:
            regime = str(row.regime or "UNKNOWN")
            regime_distribution[regime] = regime_distribution.get(regime, 0) + 1
            flags = _flags(row)
            for flag in flags:
                risk_flag_counts[flag] = risk_flag_counts.get(flag, 0) + 1
            if row.memory_adjusted_probability <= 0.0 or row.memory_adjusted_effective_size <= 0.0 or row.drift_adjusted_ev <= 0.0:
                blocked += 1
            if str(row.advisory_risk_level).upper() in {"HIGH", "CRITICAL"} or len(flags) > 0:
                over_risk += 1

        def avg(values: list[float]) -> float:
            clean = [value for value in values if isfinite(value)]
            return 0.0 if not clean else round(sum(clean) / len(clean), 6)

        return ShadowDecisionSummary(
            sample_count=count,
            avg_memory_adjusted_probability=avg([_finite_float(row.memory_adjusted_probability) for row in rows]),
            avg_effective_size=avg([_finite_float(row.memory_adjusted_effective_size) for row in rows]),
            avg_adjusted_ev=avg([_finite_float(row.uncertainty_adjusted_value) for row in rows]),
            avg_drift_adjusted_ev=avg([_finite_float(row.drift_adjusted_ev) for row in rows]),
            over_risk_rate=round(over_risk / count, 6),
            blocked_rate=round(blocked / count, 6),
            regime_distribution=dict(sorted(regime_distribution.items())),
            risk_flag_counts=dict(sorted(risk_flag_counts.items())),
        )
