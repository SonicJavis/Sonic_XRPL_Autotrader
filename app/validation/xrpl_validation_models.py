from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from math import isfinite


def _finite(raw: object, *, default: float = 0.0) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return default
    return value if isfinite(value) else default


def _unit(raw: object, *, default: float = 0.0) -> float:
    return max(0.0, min(1.0, _finite(raw, default=default)))


def _non_negative(raw: object, *, default: float = 0.0) -> float:
    return max(0.0, _finite(raw, default=default))


def _utc(raw: object) -> datetime:
    if isinstance(raw, datetime):
        value = raw
    else:
        value = datetime.fromtimestamp(0, tz=timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@dataclass(slots=True)
class XRPLShadowPrediction:
    decision_id: int
    token_id: int
    issuer: str
    ledger_index_start: int
    predicted_probability: float
    predicted_effective_size: float
    predicted_ev: float
    predicted_path_complexity: int
    predicted_route_instability: float
    predicted_competition_penalty: float
    predicted_regime: str
    predicted_confidence: float
    created_at: datetime
    requested_size: float = 0.0
    predicted_liquidity: float = 0.0
    predicted_latency_ms: float = 0.0

    def __post_init__(self) -> None:
        self.decision_id = max(0, int(_finite(self.decision_id)))
        self.token_id = max(0, int(_finite(self.token_id)))
        self.issuer = str(self.issuer)
        self.ledger_index_start = max(0, int(_finite(self.ledger_index_start)))
        self.predicted_probability = _unit(self.predicted_probability)
        self.predicted_effective_size = _non_negative(self.predicted_effective_size)
        self.predicted_ev = _finite(self.predicted_ev)
        self.predicted_path_complexity = max(0, int(_finite(self.predicted_path_complexity)))
        self.predicted_route_instability = _unit(self.predicted_route_instability)
        self.predicted_competition_penalty = _unit(self.predicted_competition_penalty)
        self.predicted_regime = str(self.predicted_regime or "UNKNOWN")
        self.predicted_confidence = _unit(self.predicted_confidence)
        self.created_at = _utc(self.created_at)
        self.requested_size = _non_negative(self.requested_size or self.predicted_effective_size)
        self.predicted_liquidity = _non_negative(self.predicted_liquidity or self.predicted_effective_size)
        self.predicted_latency_ms = _non_negative(self.predicted_latency_ms)

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        return data


@dataclass(slots=True)
class XRPLObservedOutcomeWindow:
    token_id: int
    issuer: str
    start_ledger: int
    end_ledger: int
    max_possible_fill: float
    min_possible_fill: float
    avg_possible_fill: float
    liquidity_decay_curve: list[float] = field(default_factory=list)
    price_drift_curve: list[float] = field(default_factory=list)
    route_changes_count: int = 0
    competition_events_proxy: float = 0.0
    latency_distribution_ms: list[float] = field(default_factory=list)
    observed_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))

    def __post_init__(self) -> None:
        self.token_id = max(0, int(_finite(self.token_id)))
        self.issuer = str(self.issuer)
        self.start_ledger = max(0, int(_finite(self.start_ledger)))
        self.end_ledger = max(self.start_ledger, int(_finite(self.end_ledger)))
        self.max_possible_fill = _non_negative(self.max_possible_fill)
        self.min_possible_fill = _non_negative(min(self.min_possible_fill, self.max_possible_fill))
        self.avg_possible_fill = _non_negative(min(self.avg_possible_fill, self.max_possible_fill))
        self.liquidity_decay_curve = [_non_negative(item) for item in self.liquidity_decay_curve]
        self.price_drift_curve = [_finite(item) for item in self.price_drift_curve]
        self.route_changes_count = max(0, int(_finite(self.route_changes_count)))
        self.competition_events_proxy = _unit(self.competition_events_proxy)
        self.latency_distribution_ms = [_non_negative(item) for item in self.latency_distribution_ms]
        self.observed_at = _utc(self.observed_at)

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["observed_at"] = self.observed_at.isoformat()
        return data


@dataclass(slots=True)
class XRPLValidationResult:
    decision_id: int
    fill_probability_error: float
    effective_size_error: float
    ev_error: float
    liquidity_disappearance: float
    path_failure_rate: float
    competition_miss_rate: float
    latency_miss: float
    regime_mismatch: bool
    disagreement_score: float
    brier_score: float
    overconfidence_flag: bool
    underconfidence_flag: bool
    confidence_error: float
    error_attribution: str
    is_shadow: bool = True
    is_advisory: bool = True
    is_executable: bool = False
    is_truth: bool = False

    def __post_init__(self) -> None:
        self.decision_id = max(0, int(_finite(self.decision_id)))
        self.fill_probability_error = _unit(self.fill_probability_error)
        self.effective_size_error = _unit(self.effective_size_error)
        self.ev_error = _unit(self.ev_error)
        self.liquidity_disappearance = _unit(self.liquidity_disappearance)
        self.path_failure_rate = _unit(self.path_failure_rate)
        self.competition_miss_rate = _unit(self.competition_miss_rate)
        self.latency_miss = _unit(self.latency_miss)
        self.regime_mismatch = bool(self.regime_mismatch)
        self.disagreement_score = _unit(self.disagreement_score)
        self.brier_score = _unit(self.brier_score)
        self.overconfidence_flag = bool(self.overconfidence_flag)
        self.underconfidence_flag = bool(self.underconfidence_flag)
        self.confidence_error = _unit(self.confidence_error)
        self.error_attribution = str(self.error_attribution or "unknown")
        self.is_shadow = True
        self.is_advisory = True
        self.is_executable = False
        self.is_truth = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
