"""Unified XRPL execution feasibility scoring from funded snapshots.

The layer is deterministic and read-only. It combines normalized funded
orderbook depth with route uncertainty context, but it does not approve,
construct, authorize, or broadcast anything.
"""

from __future__ import annotations

from math import isfinite, sqrt
from typing import Any, Iterable, Mapping


FEASIBILITY_SCHEMA_VERSION = "1.0"
XRPL_EXECUTION_FEASIBILITY_WARNING = (
    "Feasibility is advisory only; XRPL routing and fills are not guaranteed"
)
SAFE_SLIPPAGE_THRESHOLD = 0.08
HARD_SLIPPAGE_THRESHOLD = 0.15
CRITICAL_FAILURE_MODES = {
    "NO_PATH_AVAILABLE",
    "NO_FUNDED_LIQUIDITY",
    "MALFORMED_INPUT",
    "NON_FINITE_NUMERIC_VALUE",
}


def evaluate_execution_feasibility(
    *,
    source_asset: Mapping[str, object],
    destination_asset: Mapping[str, object],
    requested_size: float,
    normalized_orderbooks: Iterable[Mapping[str, object]],
    pathfinding_result: Mapping[str, object],
    signal_strength: float | None = None,
) -> dict[str, object]:
    requested = _finite(requested_size, default=-1.0)
    source = _asset(source_asset)
    destination = _asset(destination_asset)
    malformed = requested <= 0.0 or not source["currency"] or not destination["currency"]
    books = [book for book in normalized_orderbooks if isinstance(book, Mapping)]
    path = dict(pathfinding_result) if isinstance(pathfinding_result, Mapping) else {}
    route_type = _route_type(path)

    if malformed or not path:
        return _avoid_result(
            source,
            destination,
            max(0.0, requested),
            route_type="none",
            reason="malformed_input",
            modes=["MALFORMED_INPUT"],
            signal_strength=signal_strength,
        )

    liquidity = _liquidity_components(books, requested)
    weakest_hop_capacity = _non_negative(path.get("path_capacity", liquidity["funded_depth"]))
    expected_slippage = _unit(path.get("estimated_slippage", 0.0))
    path_viability = _unit(path.get("path_viability_score", 0.0))
    path_uncertainty = _unit(path.get("uncertainty_score", 1.0), default=1.0)
    fragility_risk = _unit(path.get("liquidity_fragility_score", 1.0), default=1.0)
    path_fragmentation = _unit(path.get("liquidity_fragmentation_score", 1.0), default=1.0)
    fragmentation_risk = _unit((path_fragmentation * 0.35) + (liquidity["fragmentation"] * 0.65))
    failure_modes = _relevant_failure_modes(
        [str(mode) for mode in path.get("failure_modes", []) if str(mode)],
        route_type,
    )

    no_route = route_type == "none" or path_viability <= 0.0
    if liquidity["funded_depth"] <= 0.0:
        failure_modes.append("NO_FUNDED_LIQUIDITY")
    if weakest_hop_capacity <= 0.0:
        failure_modes.append("WEAKEST_HOP_CAPACITY_ZERO")
    if expected_slippage > HARD_SLIPPAGE_THRESHOLD:
        failure_modes.append("EXTREME_SLIPPAGE")
    if no_route:
        failure_modes.append("NO_PATH_AVAILABLE")

    route_baseline = {"direct": 1.0, "xrp_bridge": 0.78, "multi_hop": 0.62, "none": 0.0}.get(route_type, 0.0)
    liquidity_score = _unit(
        liquidity["capacity_ratio"]
        * (1.0 - min(0.35, liquidity["level_penalty"]))
        * (1.0 - min(0.25, liquidity["fragmentation"] * 0.35))
    )
    path_reliability_score = min(
        path_viability,
        _unit(route_baseline * (1.0 - (path_uncertainty * 0.45)) * _failure_multiplier(failure_modes)),
    )
    fill_confidence_score = _unit(min(1.0, weakest_hop_capacity / max(requested, 1e-12)))
    fill_confidence_score *= {"direct": 1.0, "xrp_bridge": 0.88, "multi_hop": 0.76, "none": 0.0}.get(route_type, 0.0)
    fill_confidence_score *= 1.0 - min(0.45, (fragility_risk * 0.22) + (fragmentation_risk * 0.18) + (expected_slippage * 0.50))
    fill_confidence_score = _unit(fill_confidence_score)
    expected_fill_ratio = min(fill_confidence_score, _unit(liquidity["funded_depth"] / max(requested, 1e-12)))

    slippage_risk_score = _unit(expected_slippage / HARD_SLIPPAGE_THRESHOLD)
    slippage_risk_score = _unit(slippage_risk_score + (liquidity["quality_levels_required"] * 0.025) + _route_slippage_addon(route_type))
    fragility_risk_score = _unit(fragility_risk)
    fragmentation_risk_score = _unit(fragmentation_risk)

    critical = _has_critical_failure(failure_modes) or expected_fill_ratio <= 0.0 or weakest_hop_capacity <= 0.0
    score = (
        liquidity_score
        * path_reliability_score
        * fill_confidence_score
        * (1.0 - slippage_risk_score)
        * (1.0 - fragility_risk_score)
        * (1.0 - fragmentation_risk_score)
    )
    execution_feasibility_score = 0.0 if critical else _unit(score)
    decision, avoid_reason = _decision(
        score=execution_feasibility_score,
        expected_fill_ratio=expected_fill_ratio,
        expected_slippage=expected_slippage,
        route_type=route_type,
        failure_modes=failure_modes,
    )

    strength = None if signal_strength is None else _unit(signal_strength)
    adjusted_signal = None if strength is None else _round(strength * execution_feasibility_score)
    return _result(
        source=source,
        destination=destination,
        requested_size=requested,
        liquidity_score=liquidity_score,
        path_reliability_score=path_reliability_score,
        fill_confidence_score=fill_confidence_score,
        slippage_risk_score=slippage_risk_score,
        fragility_risk_score=fragility_risk_score,
        fragmentation_risk_score=fragmentation_risk_score,
        execution_feasibility_score=execution_feasibility_score,
        confidence_adjusted_signal=adjusted_signal,
        route_type=route_type,
        expected_fill_ratio=expected_fill_ratio,
        expected_slippage=expected_slippage,
        weakest_hop_capacity=weakest_hop_capacity,
        quality_levels_required=liquidity["quality_levels_required"],
        decision=decision,
        avoid_reason=avoid_reason,
        failure_modes=failure_modes,
    )


def _liquidity_components(books: Iterable[Mapping[str, object]], requested_size: float) -> dict[str, float | int]:
    offers: list[Mapping[str, object]] = []
    for book in books:
        raw_offers = book.get("offers", [])
        if isinstance(raw_offers, list):
            offers.extend(row for row in raw_offers if isinstance(row, Mapping))

    funded_depth = sum(_non_negative(offer.get("effective_gets")) for offer in offers)
    remaining = max(0.0, requested_size)
    levels_required = 0
    consumed_depths: list[float] = []
    for offer in sorted(offers, key=lambda row: _non_negative(row.get("quality"))):
        if remaining <= 0.0:
            break
        depth = _non_negative(offer.get("effective_gets"))
        if depth <= 0.0:
            continue
        consumed = min(depth, remaining)
        consumed_depths.append(consumed)
        remaining -= consumed
        levels_required += 1

    capacity_ratio = _unit(funded_depth / max(requested_size, 1e-12))
    level_penalty = _unit(max(0, levels_required - 1) / 8.0)
    fragmentation = _depth_fragmentation(consumed_depths)
    return {
        "funded_depth": _round(funded_depth),
        "capacity_ratio": _round(capacity_ratio),
        "quality_levels_required": int(levels_required),
        "level_penalty": _round(level_penalty),
        "fragmentation": _round(fragmentation),
    }


def _depth_fragmentation(depths: list[float]) -> float:
    if not depths:
        return 1.0
    if len(depths) == 1:
        return 0.0
    total = sum(depths)
    if total <= 0.0:
        return 1.0
    mean = total / len(depths)
    variance = sum((depth - mean) ** 2 for depth in depths) / len(depths)
    uneven = _unit((sqrt(variance) / mean) if mean > 0.0 else 1.0)
    level_pressure = _unit((len(depths) - 1) / 8.0)
    return _unit((0.60 * uneven) + (0.40 * level_pressure))


def _route_type(path: Mapping[str, object]) -> str:
    selected = str(path.get("selected_path", "")).lower()
    hops = int(_finite(path.get("estimated_hops", 0)))
    if selected == "direct" or hops == 1:
        return "direct"
    if selected == "xrp_bridge":
        return "xrp_bridge"
    if selected.startswith("multi_hop") or hops > 1:
        return "multi_hop"
    return "none"


def _decision(*, score: float, expected_fill_ratio: float, expected_slippage: float, route_type: str, failure_modes: list[str]) -> tuple[str, str | None]:
    if route_type == "none" or _has_critical_failure(failure_modes):
        return "avoid", _avoid_reason(failure_modes, "no_viable_route")
    if expected_slippage > HARD_SLIPPAGE_THRESHOLD:
        return "avoid", "slippage_above_hard_threshold"
    if expected_fill_ratio <= 0.0:
        return "avoid", "expected_fill_ratio_zero"
    if score >= 0.70 and expected_fill_ratio >= 0.80 and expected_slippage <= SAFE_SLIPPAGE_THRESHOLD and not failure_modes:
        return "feasible", None
    if score >= 0.40 and not _has_critical_failure(failure_modes):
        return "marginal", None
    return "avoid", _avoid_reason(failure_modes, "feasibility_score_low")


def _relevant_failure_modes(raw_modes: list[str], route_type: str) -> list[str]:
    ignored_by_route = {
        "direct": {"NO_BRIDGE_PATH", "NO_LIMITED_MULTI_HOP_PATH"},
        "xrp_bridge": {"NO_DIRECT_PATH", "NO_LIMITED_MULTI_HOP_PATH"},
        "multi_hop": {"NO_DIRECT_PATH", "NO_BRIDGE_PATH"},
        "none": set(),
    }.get(route_type, set())
    return sorted({mode for mode in raw_modes if mode not in ignored_by_route})


def _avoid_reason(failure_modes: list[str], fallback: str) -> str:
    if not failure_modes:
        return fallback
    preferred = [
        "MALFORMED_INPUT",
        "NO_PATH_AVAILABLE",
        "NO_FUNDED_LIQUIDITY",
        "WEAKEST_HOP_CAPACITY_ZERO",
        "EXTREME_SLIPPAGE",
        "INSUFFICIENT_CAPACITY_FOR_SIZE",
    ]
    for mode in preferred:
        if mode in failure_modes:
            return mode.lower()
    return str(failure_modes[0]).lower()


def _has_critical_failure(failure_modes: list[str]) -> bool:
    return any(mode in CRITICAL_FAILURE_MODES for mode in failure_modes)


def _failure_multiplier(failure_modes: list[str]) -> float:
    multiplier = 1.0
    for mode in failure_modes:
        if mode in CRITICAL_FAILURE_MODES:
            return 0.0
        if mode in {"WEAKEST_HOP_CAPACITY_ZERO", "EXTREME_SLIPPAGE"}:
            multiplier *= 0.20
        elif mode in {"INSUFFICIENT_CAPACITY_FOR_SIZE", "WEAKEST_HOP_BOTTLENECK"}:
            multiplier *= 0.55
        else:
            multiplier *= 0.85
    return _unit(multiplier)


def _route_slippage_addon(route_type: str) -> float:
    return {"direct": 0.0, "xrp_bridge": 0.08, "multi_hop": 0.14, "none": 1.0}.get(route_type, 1.0)


def _asset(data: Mapping[str, object]) -> dict[str, object]:
    currency = str(data.get("currency", "") or "").strip().upper()
    issuer = data.get("issuer")
    parsed_issuer = None if issuer is None else str(issuer).strip() or None
    if currency == "XRP":
        parsed_issuer = None
    return {"currency": currency, "issuer": parsed_issuer}


def _avoid_result(
    source: dict[str, object],
    destination: dict[str, object],
    requested_size: float,
    *,
    route_type: str,
    reason: str,
    modes: list[str],
    signal_strength: float | None,
) -> dict[str, object]:
    adjusted_signal = None if signal_strength is None else 0.0
    return _result(
        source=source,
        destination=destination,
        requested_size=requested_size,
        liquidity_score=0.0,
        path_reliability_score=0.0,
        fill_confidence_score=0.0,
        slippage_risk_score=1.0,
        fragility_risk_score=1.0,
        fragmentation_risk_score=1.0,
        execution_feasibility_score=0.0,
        confidence_adjusted_signal=adjusted_signal,
        route_type=route_type,
        expected_fill_ratio=0.0,
        expected_slippage=0.0,
        weakest_hop_capacity=0.0,
        quality_levels_required=0,
        decision="avoid",
        avoid_reason=reason,
        failure_modes=modes,
    )


def _result(
    *,
    source: dict[str, object],
    destination: dict[str, object],
    requested_size: float,
    liquidity_score: float,
    path_reliability_score: float,
    fill_confidence_score: float,
    slippage_risk_score: float,
    fragility_risk_score: float,
    fragmentation_risk_score: float,
    execution_feasibility_score: float,
    confidence_adjusted_signal: float | None,
    route_type: str,
    expected_fill_ratio: float,
    expected_slippage: float,
    weakest_hop_capacity: float,
    quality_levels_required: int,
    decision: str,
    avoid_reason: str | None,
    failure_modes: list[str],
) -> dict[str, object]:
    return {
        "schema_version": FEASIBILITY_SCHEMA_VERSION,
        "source_asset": source,
        "destination_asset": destination,
        "requested_size": _round(max(0.0, requested_size)),
        "liquidity_score": _round(_unit(liquidity_score)),
        "path_reliability_score": _round(_unit(path_reliability_score)),
        "fill_confidence_score": _round(_unit(fill_confidence_score)),
        "slippage_risk_score": _round(_unit(slippage_risk_score)),
        "fragility_risk_score": _round(_unit(fragility_risk_score)),
        "fragmentation_risk_score": _round(_unit(fragmentation_risk_score)),
        "execution_feasibility_score": _round(_unit(execution_feasibility_score)),
        "confidence_adjusted_signal": None if confidence_adjusted_signal is None else _round(_unit(confidence_adjusted_signal)),
        "route_type": route_type if route_type in {"direct", "xrp_bridge", "multi_hop", "none"} else "none",
        "expected_fill_ratio": _round(_unit(expected_fill_ratio)),
        "expected_slippage": _round(_unit(expected_slippage)),
        "weakest_hop_capacity": _round(max(0.0, weakest_hop_capacity)),
        "quality_levels_required": max(0, int(quality_levels_required)),
        "decision": decision if decision in {"feasible", "marginal", "avoid"} else "avoid",
        "avoid_reason": avoid_reason,
        "failure_modes": sorted(set(str(mode) for mode in failure_modes if str(mode))),
        "is_shadow": True,
        "is_advisory": True,
        "is_executable": False,
        "is_truth": False,
    }


def _finite(raw: object, *, default: float = 0.0) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return default
    return value if isfinite(value) else default


def _non_negative(raw: object, *, default: float = 0.0) -> float:
    return max(0.0, _finite(raw, default=default))


def _unit(raw: object, *, default: float = 0.0) -> float:
    return max(0.0, min(1.0, _finite(raw, default=default)))


def _round(value: float, digits: int = 6) -> float:
    if not isfinite(value):
        return 0.0
    rounded = round(value, digits)
    return 0.0 if rounded == -0.0 else rounded


__all__ = [
    "FEASIBILITY_SCHEMA_VERSION",
    "XRPL_EXECUTION_FEASIBILITY_WARNING",
    "evaluate_execution_feasibility",
]
