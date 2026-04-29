from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from math import isfinite
from statistics import mean, pstdev
from typing import Iterable, Mapping


RECOMMENDATION_SCHEMA_VERSION = "1.0"
XRPL_CALIBRATION_WARNING = (
    "Manual-review-only recommendations from probabilistic shadow validation; "
    "observations are uncertain and no settings are changed"
)

REQUIRED_UNCERTAINTY_PHRASES = (
    "observed disagreement",
    "probabilistic outcome",
    "uncertainty",
    "suggested review",
)

_WORDING_SUFFIX = (
    "This is a manual suggested review of observed disagreement under uncertainty for a probabilistic outcome."
)

_CERTAINTY_TERMS = {
    "accurate",
    "actual",
    "confirmed",
    "correct",
    "guaranteed",
    "real",
    "true",
}

_DIRECTIONS = {"increase", "decrease", "review", "dampen"}
_TARGETS = {"confidence", "penalty", "regime classifier", "weighting"}
_SOURCE_METRICS = {"overconfidence_rate", "brier_score", "attribution_cluster"}
_STRENGTHS = {"weak", "moderate", "strong"}
_CONFIDENCE_LEVELS = {"low", "medium", "high"}

RECOMMENDATION_FIELDS = tuple(
    sorted(
        {
            "confidence_level",
            "consistency_score",
            "effective_sample_size",
            "high_variance_flag",
            "is_advisory",
            "is_executable",
            "is_shadow",
            "is_truth",
            "low_sample_warning",
            "observation",
            "rationale",
            "recommendation_strength",
            "requires_manual_approval",
            "sample_decay_weight",
            "schema_version",
            "scope",
            "source_metric",
            "stability_score",
            "suggestion_direction",
            "support_size",
            "target_component",
            "type",
            "volatility_flag",
        }
    )
)


def _finite(raw: object, *, default: float = 0.0) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return default
    return value if isfinite(value) else default


def _unit(raw: object, *, default: float = 0.0) -> float:
    return max(0.0, min(1.0, _finite(raw, default=default)))


def _timestamp(raw: object) -> float:
    if isinstance(raw, datetime):
        value = raw if raw.tzinfo is not None else raw.replace(tzinfo=timezone.utc)
        return _finite(value.astimezone(timezone.utc).timestamp())
    return 0.0


@dataclass(frozen=True, slots=True)
class XRPLCalibrationRecommendation:
    type: str
    source_metric: str
    scope: dict[str, object]
    observation: str
    suggestion_direction: str
    target_component: str
    support_size: int
    effective_sample_size: int
    sample_decay_weight: float
    consistency_score: float
    stability_score: float
    volatility_flag: bool
    high_variance_flag: bool
    low_sample_warning: bool
    recommendation_strength: str
    confidence_level: str
    rationale: str
    schema_version: str = RECOMMENDATION_SCHEMA_VERSION
    requires_manual_approval: bool = True
    is_shadow: bool = True
    is_advisory: bool = True
    is_executable: bool = False
    is_truth: bool = False

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["schema_version"] = RECOMMENDATION_SCHEMA_VERSION
        data["support_size"] = max(0, int(data["support_size"]))
        data["effective_sample_size"] = max(0, int(data["effective_sample_size"]))
        data["sample_decay_weight"] = round(_unit(data["sample_decay_weight"], default=1.0), 6)
        data["consistency_score"] = round(_unit(data["consistency_score"]), 6)
        data["stability_score"] = round(_unit(data["stability_score"]), 6)
        data["volatility_flag"] = bool(data["volatility_flag"])
        data["high_variance_flag"] = bool(data["high_variance_flag"])
        data["low_sample_warning"] = bool(data["low_sample_warning"])
        data["requires_manual_approval"] = True
        data["is_shadow"] = True
        data["is_advisory"] = True
        data["is_executable"] = False
        data["is_truth"] = False
        validated = validate_recommendation_payload(data)
        return {key: validated[key] for key in RECOMMENDATION_FIELDS}


class XRPLCalibrationRecommendationEngine:
    def generate(self, rows: Iterable[object], *, min_support: int = 30) -> list[XRPLCalibrationRecommendation]:
        samples = [_Sample.from_row(row) for row in rows]
        samples = sorted((sample for sample in samples if sample is not None), key=_sample_sort_key)
        if not samples:
            return []
        min_support = max(1, int(min_support))
        recommendations: list[XRPLCalibrationRecommendation] = []
        for scope, group in _isolated_groups(samples, min_support=min_support):
            recommendations.extend(_recommend_for_group(scope, group, min_support=min_support))
        return _dedupe_and_sort(recommendations)

    def serialize(self, rows: Iterable[object], *, min_support: int = 30) -> str:
        return stable_recommendation_json(self.generate(rows, min_support=min_support))


def stable_recommendation_json(recommendations: Iterable[XRPLCalibrationRecommendation]) -> str:
    payload = [row.to_dict() for row in recommendations]
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def validate_recommendation_payload(data: Mapping[str, object]) -> dict[str, object]:
    keys = set(data)
    expected = set(RECOMMENDATION_FIELDS)
    unknown = keys - expected
    missing = expected - keys
    if unknown or missing:
        raise ValueError(f"recommendation schema mismatch: unknown={sorted(unknown)} missing={sorted(missing)}")

    payload = dict(data)
    if payload["schema_version"] != RECOMMENDATION_SCHEMA_VERSION:
        raise ValueError("unsupported recommendation schema_version")
    if payload["type"] != "calibration_recommendation":
        raise ValueError("invalid recommendation type")
    if payload["source_metric"] not in _SOURCE_METRICS:
        raise ValueError("invalid source_metric")
    if payload["suggestion_direction"] not in _DIRECTIONS:
        raise ValueError("invalid suggestion_direction")
    if payload["target_component"] not in _TARGETS:
        raise ValueError("invalid target_component")
    if payload["recommendation_strength"] not in _STRENGTHS:
        raise ValueError("invalid recommendation_strength")
    if payload["confidence_level"] not in _CONFIDENCE_LEVELS:
        raise ValueError("invalid confidence_level")
    if not isinstance(payload["scope"], dict):
        raise ValueError("scope must be a dict")
    if "token_id" not in payload["scope"] or "issuer" not in payload["scope"]:
        raise ValueError("scope must include token_id and issuer")

    for field in ("consistency_score", "sample_decay_weight", "stability_score"):
        value = _unit(payload[field])
        if not isfinite(value):
            raise ValueError(f"{field} must be finite")
        payload[field] = value
    for field in ("support_size", "effective_sample_size"):
        value = int(_finite(payload[field]))
        if value < 0:
            raise ValueError(f"{field} must be non-negative")
        payload[field] = value
    for field in (
        "high_variance_flag",
        "is_advisory",
        "is_executable",
        "is_shadow",
        "is_truth",
        "low_sample_warning",
        "requires_manual_approval",
        "volatility_flag",
    ):
        payload[field] = bool(payload[field])
    if payload["requires_manual_approval"] is not True:
        raise ValueError("requires_manual_approval must be enabled")
    if payload["is_shadow"] is not True or payload["is_advisory"] is not True:
        raise ValueError("recommendation must remain shadow advisory")
    if payload["is_executable"] is not False or payload["is_truth"] is not False:
        raise ValueError("recommendation must remain non-executable and non-truth")
    _validate_wording(str(payload["observation"]), str(payload["rationale"]))
    return payload


@dataclass(frozen=True, slots=True)
class _Sample:
    decision_id: int
    token_id: int
    issuer: str
    regime: str
    attribution: str
    disagreement_score: float
    brier_score: float
    overconfidence_flag: bool
    underconfidence_flag: bool
    regime_mismatch: bool
    liquidity_disappearance: float
    path_failure_rate: float
    competition_miss_rate: float
    latency_miss: float
    created_at_ts: float

    @staticmethod
    def from_row(row: object) -> "_Sample | None":
        token_id = max(0, int(_finite(getattr(row, "token_id", 0))))
        issuer = str(getattr(row, "issuer", "") or "")
        attribution = str(getattr(row, "attribution", "unknown") or "unknown")
        regime = str(getattr(row, "predicted_regime", "UNKNOWN") or "UNKNOWN")
        if token_id <= 0 or not issuer:
            return None
        return _Sample(
            decision_id=max(0, int(_finite(getattr(row, "decision_id", 0)))),
            token_id=token_id,
            issuer=issuer,
            regime=regime,
            attribution=attribution,
            disagreement_score=_unit(getattr(row, "disagreement_score", 0.0)),
            brier_score=_unit(getattr(row, "brier_score", 0.0)),
            overconfidence_flag=bool(getattr(row, "overconfidence_flag", False)),
            underconfidence_flag=bool(getattr(row, "underconfidence_flag", False)),
            regime_mismatch=bool(getattr(row, "regime_mismatch", False)),
            liquidity_disappearance=_unit(getattr(row, "liquidity_disappearance", 0.0)),
            path_failure_rate=_unit(getattr(row, "path_failure_rate", 0.0)),
            competition_miss_rate=_unit(getattr(row, "competition_miss_rate", 0.0)),
            latency_miss=_unit(getattr(row, "latency_miss", 0.0)),
            created_at_ts=_timestamp(getattr(row, "created_at", None)),
        )


def _sample_sort_key(sample: _Sample) -> tuple[object, ...]:
    return (
        sample.token_id,
        sample.issuer,
        sample.created_at_ts,
        sample.decision_id,
        sample.attribution,
        sample.regime,
    )


def _isolated_groups(samples: list[_Sample], *, min_support: int) -> list[tuple[dict[str, object], list[_Sample]]]:
    grouped: dict[tuple[object, ...], tuple[dict[str, object], list[_Sample]]] = {}
    for sample in samples:
        base_scope = {"token_id": sample.token_id, "issuer": sample.issuer}
        scopes = [
            {**base_scope, "attribution": sample.attribution},
            {**base_scope, "regime": sample.regime},
        ]
        if _token_support(samples, sample.token_id, sample.issuer) >= max(1, min_support // 2):
            scopes.append(base_scope)
        for scope in scopes:
            key = tuple(sorted(scope.items()))
            if key not in grouped:
                grouped[key] = (scope, [])
            grouped[key][1].append(sample)
    return sorted(grouped.values(), key=lambda item: _scope_group_sort_key(item[0], item[1]))


def _token_support(samples: list[_Sample], token_id: int, issuer: str) -> int:
    return sum(1 for sample in samples if sample.token_id == token_id and sample.issuer == issuer)


def _scope_group_sort_key(scope: dict[str, object], group: list[_Sample]) -> tuple[object, ...]:
    return (
        str(scope.get("attribution", "")),
        str(scope.get("regime", "")),
        int(scope.get("token_id", 0)),
        -len(group),
        str(scope.get("issuer", "")),
    )


def _recommend_for_group(scope: dict[str, object], group: list[_Sample], *, min_support: int) -> list[XRPLCalibrationRecommendation]:
    group = sorted(group, key=lambda sample: (sample.created_at_ts, sample.decision_id))
    support = len(group)
    weights = _decay_weights(group)
    disagreement = [sample.disagreement_score for sample in group]
    briers = [sample.brier_score for sample in group]
    over_rate = sum(1 for sample in group if sample.overconfidence_flag) / max(support, 1)
    under_rate = sum(1 for sample in group if sample.underconfidence_flag) / max(support, 1)
    mismatch_rate = sum(1 for sample in group if sample.regime_mismatch) / max(support, 1)
    avg_brier = mean(briers) if briers else 0.0
    dispersion = max(
        pstdev(disagreement) if len(disagreement) > 1 else 0.0,
        pstdev(briers) if len(briers) > 1 else 0.0,
    )
    high_variance = dispersion > 0.20
    low_sample = support < min_support
    stability = _stability_score(dispersion)
    consistency = max(over_rate, under_rate, avg_brier, mismatch_rate)
    confidence = _confidence_level(
        support=support,
        min_support=min_support,
        consistency=consistency,
        stability_score=stability,
        high_variance=high_variance,
    )
    strength = _recommendation_strength(
        support=support,
        min_support=min_support,
        consistency=consistency,
        stability_score=stability,
        high_variance=high_variance,
    )
    metrics = _GroupMetrics(
        support_size=support,
        effective_sample_size=support,
        sample_decay_weight=mean(weights) if weights else 1.0,
        high_variance_flag=high_variance,
        low_sample_warning=low_sample,
        stability_score=stability,
        recommendation_strength=strength,
        confidence_level=confidence,
    )

    recs: list[XRPLCalibrationRecommendation] = []
    directional_allowed = not high_variance and not low_sample
    if over_rate >= 0.25:
        recs.append(
            _build(
                scope,
                metrics,
                source_metric="overconfidence_rate",
                observation="Validation windows show repeated overconfidence-style observed disagreement under uncertainty.",
                suggestion_direction="decrease" if directional_allowed else "review",
                target_component="confidence",
                consistency_score=over_rate,
                rationale="Use this probabilistic outcome cluster as a suggested review for confidence scaling before any human-approved change.",
            )
        )
    if under_rate >= 0.25:
        recs.append(
            _build(
                scope,
                metrics,
                source_metric="brier_score",
                observation="Validation windows show repeated underconfidence-style observed disagreement under uncertainty.",
                suggestion_direction="increase" if directional_allowed else "review",
                target_component="confidence",
                consistency_score=under_rate,
                rationale="Use this probabilistic outcome cluster as a suggested review for confidence scaling; no setting is changed.",
            )
        )
    if avg_brier >= 0.20:
        recs.append(
            _build(
                scope,
                metrics,
                source_metric="brier_score",
                observation="Brier-style observed disagreement remains elevated across probabilistic outcome windows.",
                suggestion_direction="increase" if directional_allowed else "review",
                target_component="weighting",
                consistency_score=avg_brier,
                rationale="Use uncertainty weighting as a suggested review item when clustered disagreement remains elevated.",
            )
        )
    attribution = str(scope.get("attribution", ""))
    if attribution in _ATTRIBUTION_MAP:
        direction, target, rationale = _ATTRIBUTION_MAP[attribution]
        recs.append(
            _build(
                scope,
                metrics,
                source_metric="attribution_cluster",
                observation=f"Observed disagreement clustering points to {attribution} within a probabilistic outcome window group.",
                suggestion_direction=direction if directional_allowed else "review",
                target_component=target,
                consistency_score=min(1.0, support / max(min_support, 1)),
                rationale=rationale,
            )
        )
    if mismatch_rate >= 0.20:
        recs.append(
            _build(
                scope,
                metrics,
                source_metric="attribution_cluster",
                observation="Regime labels and observed disagreement show recurring asymmetry under uncertainty.",
                suggestion_direction="review",
                target_component="regime classifier",
                consistency_score=mismatch_rate,
                rationale="Use this probabilistic outcome cluster as a suggested review for regime sensitivity before any human-approved change.",
            )
        )
    if low_sample and not recs:
        recs.append(
            _build(
                scope,
                metrics,
                source_metric="brier_score",
                observation="Sample support is below the review threshold; observed disagreement may reflect noise under uncertainty.",
                suggestion_direction="review",
                target_component="weighting",
                consistency_score=max(avg_brier, mean(disagreement) if disagreement else 0.0),
                rationale="Collect more probabilistic outcome windows before treating this suggested review as systematic.",
            )
        )
    return recs


@dataclass(frozen=True, slots=True)
class _GroupMetrics:
    support_size: int
    effective_sample_size: int
    sample_decay_weight: float
    high_variance_flag: bool
    low_sample_warning: bool
    stability_score: float
    recommendation_strength: str
    confidence_level: str


def _decay_weights(group: list[_Sample]) -> list[float]:
    if not group:
        return []
    timestamps = [sample.created_at_ts for sample in group]
    newest = max(timestamps)
    oldest = min(timestamps)
    span = max(newest - oldest, 1.0)
    return [max(0.25, 1.0 - 0.50 * ((newest - sample.created_at_ts) / span)) for sample in group]


def _stability_score(dispersion: float) -> float:
    return round(max(0.0, min(1.0, 1.0 - (_unit(dispersion) * 2.0))), 6)


def _build(
    scope: dict[str, object],
    metrics: _GroupMetrics,
    *,
    source_metric: str,
    observation: str,
    suggestion_direction: str,
    target_component: str,
    consistency_score: float,
    rationale: str,
) -> XRPLCalibrationRecommendation:
    return XRPLCalibrationRecommendation(
        type="calibration_recommendation",
        source_metric=source_metric,
        scope=dict(sorted(scope.items())),
        observation=_with_required_framing(observation),
        suggestion_direction=suggestion_direction,
        target_component=target_component,
        support_size=metrics.support_size,
        effective_sample_size=metrics.effective_sample_size,
        sample_decay_weight=_unit(metrics.sample_decay_weight, default=1.0),
        consistency_score=_unit(consistency_score),
        stability_score=_unit(metrics.stability_score),
        volatility_flag=metrics.high_variance_flag,
        high_variance_flag=metrics.high_variance_flag,
        low_sample_warning=metrics.low_sample_warning,
        recommendation_strength=metrics.recommendation_strength,
        confidence_level=metrics.confidence_level,
        rationale=_with_required_framing(rationale),
    )


def _with_required_framing(text: str) -> str:
    return f"{text} {_WORDING_SUFFIX}"


def _confidence_level(
    *,
    support: int,
    min_support: int,
    consistency: float,
    stability_score: float,
    high_variance: bool,
) -> str:
    if support < min_support or high_variance:
        return "low"
    if consistency >= 0.65 and support >= min_support * 2 and stability_score >= 0.80:
        return "high"
    return "medium"


def _recommendation_strength(
    *,
    support: int,
    min_support: int,
    consistency: float,
    stability_score: float,
    high_variance: bool,
) -> str:
    if support < min_support or high_variance:
        return "weak"
    if support >= min_support * 2 and consistency >= 0.65 and stability_score >= 0.80:
        return "strong"
    if consistency >= 0.35 and stability_score >= 0.60:
        return "moderate"
    return "weak"


def _dedupe_and_sort(recommendations: list[XRPLCalibrationRecommendation]) -> list[XRPLCalibrationRecommendation]:
    seen: set[tuple[str, str, tuple[tuple[str, object], ...], str]] = set()
    rows: list[XRPLCalibrationRecommendation] = []
    for rec in recommendations:
        key = (rec.source_metric, rec.target_component, tuple(sorted(rec.scope.items())), rec.suggestion_direction)
        if key in seen:
            continue
        seen.add(key)
        rows.append(rec)
    return sorted(rows, key=_recommendation_sort_key)


def _recommendation_sort_key(rec: XRPLCalibrationRecommendation) -> tuple[object, ...]:
    return (
        str(rec.scope.get("attribution", "")),
        str(rec.scope.get("regime", "")),
        int(rec.scope.get("token_id", 0)),
        -int(rec.support_size),
        str(rec.scope.get("issuer", "")),
        rec.source_metric,
        rec.target_component,
        rec.suggestion_direction,
    )


def _validate_wording(observation: str, rationale: str) -> None:
    text = f"{observation} {rationale}".lower()
    tokens = {token.strip(".,;:!?()[]{}\"'") for token in text.split()}
    blocked = sorted(_CERTAINTY_TERMS.intersection(tokens))
    if blocked:
        raise ValueError(f"certainty language is not allowed: {blocked}")
    missing = [phrase for phrase in REQUIRED_UNCERTAINTY_PHRASES if phrase not in text]
    if missing:
        raise ValueError(f"uncertainty framing missing: {missing}")


_ATTRIBUTION_MAP = {
    "liquidity_illusion": (
        "increase",
        "penalty",
        "Use liquidity-observation disagreement as a suggested review for penalty weighting; liquidity observations remain non-executable under uncertainty.",
    ),
    "latency": (
        "increase",
        "weighting",
        "Use ledger-latency sensitivity as a suggested review for uncertainty weighting in this probabilistic outcome scope.",
    ),
    "path_instability": (
        "increase",
        "penalty",
        "Use path-instability disagreement as a suggested review for penalty weighting across probabilistic outcome windows.",
    ),
    "competition": (
        "increase",
        "penalty",
        "Use competition-proxy disagreement as a suggested review for penalty weighting under uncertainty.",
    ),
    "regime_shift": (
        "review",
        "regime classifier",
        "Use recurring regime-shift attribution as a suggested review for classifier sensitivity under uncertainty.",
    ),
}
