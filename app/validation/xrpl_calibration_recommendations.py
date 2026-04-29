from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from statistics import mean, pstdev
from typing import Iterable


XRPL_CALIBRATION_WARNING = (
    "Manual-review-only recommendations from probabilistic shadow validation; observations are uncertain and no settings are changed"
)


def _finite(raw: object, *, default: float = 0.0) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return default
    return value if isfinite(value) else default


def _unit(raw: object, *, default: float = 0.0) -> float:
    return max(0.0, min(1.0, _finite(raw, default=default)))


@dataclass(frozen=True, slots=True)
class XRPLCalibrationRecommendation:
    type: str
    source_metric: str
    scope: dict[str, object]
    observation: str
    suggestion_direction: str
    target_component: str
    support_size: int
    consistency_score: float
    volatility_flag: bool
    confidence_level: str
    rationale: str
    requires_manual_approval: bool = True
    is_shadow: bool = True
    is_advisory: bool = True
    is_executable: bool = False
    is_truth: bool = False

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["support_size"] = max(0, int(data["support_size"]))
        data["consistency_score"] = _unit(data["consistency_score"])
        data["volatility_flag"] = bool(data["volatility_flag"])
        data["requires_manual_approval"] = True
        data["is_shadow"] = True
        data["is_advisory"] = True
        data["is_executable"] = False
        data["is_truth"] = False
        return data


class XRPLCalibrationRecommendationEngine:
    def generate(self, rows: Iterable[object], *, min_support: int = 30) -> list[XRPLCalibrationRecommendation]:
        samples = [_Sample.from_row(row) for row in rows]
        samples = [sample for sample in samples if sample is not None]
        if not samples:
            return []
        min_support = max(1, int(min_support))
        recommendations: list[XRPLCalibrationRecommendation] = []
        groups: list[tuple[dict[str, object], list[_Sample]]] = []
        groups.extend(({"attribution": key}, value) for key, value in _group(samples, lambda item: item.attribution).items())
        groups.extend(({"regime": key}, value) for key, value in _group(samples, lambda item: item.regime).items())
        token_groups = _group(samples, lambda item: str(item.token_id))
        groups.extend(({"token_id": int(key)}, value) for key, value in token_groups.items() if len(value) >= max(1, min_support // 2))
        for scope, group in groups:
            recommendations.extend(_recommend_for_group(scope, group, min_support=min_support))
        return _dedupe_and_sort(recommendations)


@dataclass(frozen=True, slots=True)
class _Sample:
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

    @staticmethod
    def from_row(row: object) -> "_Sample | None":
        token_id = max(0, int(_finite(getattr(row, "token_id", 0))))
        attribution = str(getattr(row, "attribution", "unknown") or "unknown")
        regime = str(getattr(row, "predicted_regime", "UNKNOWN") or "UNKNOWN")
        if token_id <= 0 and attribution == "unknown" and regime == "UNKNOWN":
            return None
        return _Sample(
            token_id=token_id,
            issuer=str(getattr(row, "issuer", "")),
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
        )


def _group(samples: list[_Sample], key_fn) -> dict[str, list[_Sample]]:
    grouped: dict[str, list[_Sample]] = {}
    for sample in samples:
        grouped.setdefault(str(key_fn(sample)), []).append(sample)
    return dict(sorted(grouped.items()))


def _recommend_for_group(scope: dict[str, object], group: list[_Sample], *, min_support: int) -> list[XRPLCalibrationRecommendation]:
    support = len(group)
    disagreement = [sample.disagreement_score for sample in group]
    briers = [sample.brier_score for sample in group]
    over_rate = sum(1 for sample in group if sample.overconfidence_flag) / max(support, 1)
    under_rate = sum(1 for sample in group if sample.underconfidence_flag) / max(support, 1)
    mismatch_rate = sum(1 for sample in group if sample.regime_mismatch) / max(support, 1)
    avg_brier = mean(briers) if briers else 0.0
    volatility = (pstdev(disagreement) if len(disagreement) > 1 else 0.0) > 0.20 or (pstdev(briers) if len(briers) > 1 else 0.0) > 0.20
    confidence = _confidence_level(support=support, min_support=min_support, consistency=max(over_rate, under_rate, avg_brier, mismatch_rate), volatility=volatility)
    recs: list[XRPLCalibrationRecommendation] = []
    if over_rate >= 0.25:
        recs.append(
            _build(
                scope,
                source_metric="overconfidence_rate",
                observation="Validation windows show repeated overconfidence-style disagreement under uncertainty.",
                suggestion_direction="review" if volatility else "decrease",
                target_component="confidence",
                support_size=support,
                consistency_score=over_rate,
                volatility_flag=volatility,
                confidence_level=confidence,
                rationale="Consider decreasing confidence scaling for this scope until more shadow validation support is reviewed.",
            )
        )
    if under_rate >= 0.25:
        recs.append(
            _build(
                scope,
                source_metric="brier_score",
                observation="Validation windows show repeated underconfidence-style disagreement under uncertainty.",
                suggestion_direction="review" if volatility else "increase",
                target_component="confidence",
                support_size=support,
                consistency_score=under_rate,
                volatility_flag=volatility,
                confidence_level=confidence,
                rationale="Consider reviewing whether confidence scaling is too conservative for this scope; manual approval is required.",
            )
        )
    if avg_brier >= 0.20:
        recs.append(
            _build(
                scope,
                source_metric="brier_score",
                observation="Brier-style disagreement remains elevated across the outcome-window samples.",
                suggestion_direction="review" if volatility else "increase",
                target_component="weighting",
                support_size=support,
                consistency_score=avg_brier,
                volatility_flag=volatility,
                confidence_level=confidence,
                rationale="Consider increasing uncertainty weighting or dampening interpretation strength when the cluster is volatile.",
            )
        )
    attribution = str(scope.get("attribution", ""))
    if attribution in _ATTRIBUTION_MAP:
        direction, target, rationale = _ATTRIBUTION_MAP[attribution]
        recs.append(
            _build(
                scope,
                source_metric="attribution_cluster",
                observation=f"Attribution clustering points to {attribution} as a recurring disagreement dimension.",
                suggestion_direction="review" if volatility else direction,
                target_component=target,
                support_size=support,
                consistency_score=min(1.0, support / max(min_support, 1)),
                volatility_flag=volatility,
                confidence_level=confidence,
                rationale=rationale,
            )
        )
    if mismatch_rate >= 0.20:
        recs.append(
            _build(
                scope,
                source_metric="attribution_cluster",
                observation="Regime labels and outcome-window disagreement show recurring asymmetry under uncertainty.",
                suggestion_direction="review",
                target_component="regime classifier",
                support_size=support,
                consistency_score=mismatch_rate,
                volatility_flag=volatility,
                confidence_level=confidence,
                rationale="Review regime classification sensitivity for this scope before any human-approved calibration change.",
            )
        )
    if support < min_support and not recs:
        recs.append(
            _build(
                scope,
                source_metric="brier_score",
                observation="Sample support is below the review threshold; any pattern may reflect noise.",
                suggestion_direction="review",
                target_component="weighting",
                support_size=support,
                consistency_score=max(avg_brier, mean(disagreement) if disagreement else 0.0),
                volatility_flag=volatility,
                confidence_level="low",
                rationale="Collect more shadow validation windows before interpreting this scope as systematic.",
            )
        )
    return recs


def _build(
    scope: dict[str, object],
    *,
    source_metric: str,
    observation: str,
    suggestion_direction: str,
    target_component: str,
    support_size: int,
    consistency_score: float,
    volatility_flag: bool,
    confidence_level: str,
    rationale: str,
) -> XRPLCalibrationRecommendation:
    return XRPLCalibrationRecommendation(
        type="calibration_recommendation",
        source_metric=source_metric,
        scope=dict(sorted(scope.items())),
        observation=observation,
        suggestion_direction=suggestion_direction,
        target_component=target_component,
        support_size=support_size,
        consistency_score=_unit(consistency_score),
        volatility_flag=volatility_flag,
        confidence_level=confidence_level,
        rationale=rationale,
    )


def _confidence_level(*, support: int, min_support: int, consistency: float, volatility: bool) -> str:
    if support < min_support or volatility:
        return "low"
    if consistency >= 0.65 and support >= min_support * 2:
        return "high"
    return "medium"


def _dedupe_and_sort(recommendations: list[XRPLCalibrationRecommendation]) -> list[XRPLCalibrationRecommendation]:
    seen: set[tuple[str, str, tuple[tuple[str, object], ...], str]] = set()
    rows: list[XRPLCalibrationRecommendation] = []
    for rec in recommendations:
        key = (rec.source_metric, rec.target_component, tuple(sorted(rec.scope.items())), rec.suggestion_direction)
        if key in seen:
            continue
        seen.add(key)
        rows.append(rec)
    return sorted(rows, key=lambda rec: (str(rec.scope), rec.source_metric, rec.target_component, rec.suggestion_direction))


_ATTRIBUTION_MAP = {
    "liquidity_illusion": (
        "increase",
        "penalty",
        "Consider increasing penalty weight for liquidity-observation disagreement; liquidity observations remain non-executable.",
    ),
    "latency": (
        "increase",
        "weighting",
        "Consider increasing uncertainty weighting for ledger-latency sensitivity in this scope.",
    ),
    "path_instability": (
        "increase",
        "penalty",
        "Consider increasing penalty weight for path instability patterns across outcome windows.",
    ),
    "competition": (
        "increase",
        "penalty",
        "Consider increasing penalty weight for competition-proxy disagreement; invisible competition remains uncertain.",
    ),
    "regime_shift": (
        "review",
        "regime classifier",
        "Review regime classification sensitivity for recurring regime-shift attribution.",
    ),
}
