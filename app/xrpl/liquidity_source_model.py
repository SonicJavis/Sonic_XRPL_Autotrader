"""XRPL orderbook, AMM, and hybrid liquidity source scoring.

This module is pure and read-only. It consumes already-normalized orderbook
state, path uncertainty, execution feasibility, and optional AMM snapshots.
"""

from __future__ import annotations

from math import isfinite
from typing import Any, Iterable, Mapping


LIQUIDITY_SOURCE_SCHEMA_VERSION = "1.0"
XRPL_LIQUIDITY_SOURCE_WARNING = (
    "Liquidity source scoring is advisory only; XRPL orderbook and AMM conditions change per ledger"
)
AMM_HARD_IMPACT_THRESHOLD = 0.25
AMM_MARGINAL_IMPACT_THRESHOLD = 0.10


def evaluate_liquidity_sources(
    *,
    source_asset: Mapping[str, object],
    destination_asset: Mapping[str, object],
    requested_size: float,
    normalized_orderbooks: Iterable[Mapping[str, object]],
    pathfinding_result: Mapping[str, object],
    execution_feasibility: Mapping[str, object],
    amm_snapshot: Mapping[str, object] | None = None,
) -> dict[str, object]:
    source = _asset(source_asset)
    destination = _asset(destination_asset)
    requested = _finite(requested_size, default=-1.0)
    feasibility = dict(execution_feasibility) if isinstance(execution_feasibility, Mapping) else {}
    path = dict(pathfinding_result) if isinstance(pathfinding_result, Mapping) else {}
    books = [book for book in normalized_orderbooks if isinstance(book, Mapping)]

    malformed = requested <= 0.0 or not source["currency"] or not destination["currency"]
    orderbook_score = _unit(feasibility.get("execution_feasibility_score", 0.0))
    orderbook_fill_ratio = _unit(feasibility.get("expected_fill_ratio", 0.0))
    orderbook_impact = _unit(feasibility.get("expected_slippage", 0.0))
    orderbook_available = bool(
        books
        and feasibility.get("decision") in {"feasible", "marginal"}
        and orderbook_score > 0.0
        and orderbook_fill_ratio > 0.0
        and str(feasibility.get("route_type", "none")) != "none"
    )

    amm = _evaluate_amm(source, destination, requested, amm_snapshot)
    amm_available = bool(amm["available"])
    amm_score = float(amm["score"])
    hybrid_possible = orderbook_available and amm_available
    hybrid_score = max(orderbook_score, amm_score) if hybrid_possible else 0.0

    liquidity_source = _liquidity_source(orderbook_available, amm_available)
    preferred_source = _preferred_source(
        orderbook_available=orderbook_available,
        amm_available=amm_available,
        orderbook_score=orderbook_score,
        amm_score=amm_score,
        orderbook_impact=orderbook_impact,
        amm_impact=float(amm["price_impact"]),
        orderbook_fill=orderbook_fill_ratio,
        amm_fill=float(amm["fill_ratio"]),
    )
    expected_price_impact, expected_fill_ratio = _preferred_metrics(
        preferred_source=preferred_source,
        orderbook_impact=orderbook_impact,
        amm_impact=float(amm["price_impact"]),
        orderbook_fill=orderbook_fill_ratio,
        amm_fill=float(amm["fill_ratio"]),
    )

    warnings = []
    if malformed:
        warnings.append("MALFORMED_INPUT")
    if not orderbook_available:
        warnings.append("ORDERBOOK_NOT_USABLE")
    if amm_snapshot is None:
        warnings.append("AMM_UNAVAILABLE")
    elif not amm_available:
        warnings.extend(str(item) for item in amm["warnings"])
    if hybrid_possible:
        warnings.append("HYBRID_POSSIBLE_NOT_OPTIMIZED")
    if expected_price_impact > AMM_MARGINAL_IMPACT_THRESHOLD:
        warnings.append("HIGH_PRICE_IMPACT")

    decision, avoid_reason = _decision(
        malformed=malformed,
        source=liquidity_source,
        expected_fill_ratio=expected_fill_ratio,
        expected_price_impact=expected_price_impact,
        orderbook_available=orderbook_available,
        amm_available=amm_available,
    )

    return {
        "schema_version": LIQUIDITY_SOURCE_SCHEMA_VERSION,
        "liquidity_source": liquidity_source,
        "orderbook_available": orderbook_available,
        "amm_available": amm_available,
        "hybrid_possible": hybrid_possible,
        "preferred_source": preferred_source,
        "orderbook_score": _round(orderbook_score),
        "amm_score": _round(amm_score),
        "hybrid_score": _round(hybrid_score),
        "expected_price_impact": _round(_unit(expected_price_impact)),
        "expected_fill_ratio": _round(_unit(expected_fill_ratio)),
        "amm_price_impact": _round(_unit(amm["price_impact"])),
        "amm_fill_ratio": _round(_unit(amm["fill_ratio"])),
        "amm_effective_price": _round(_non_negative(amm["effective_price"])),
        "liquidity_warnings": sorted(set(warnings)),
        "decision": decision,
        "avoid_reason": avoid_reason,
        "is_shadow": True,
        "is_advisory": True,
        "is_executable": False,
        "is_truth": False,
        "xrpl_warning": XRPL_LIQUIDITY_SOURCE_WARNING,
    }


def _evaluate_amm(
    source: dict[str, object],
    destination: dict[str, object],
    requested_size: float,
    amm_snapshot: Mapping[str, object] | None,
) -> dict[str, object]:
    if not isinstance(amm_snapshot, Mapping):
        return _amm_unavailable(["AMM_UNAVAILABLE"])

    asset1 = _asset(amm_snapshot.get("asset1") if isinstance(amm_snapshot.get("asset1"), Mapping) else {})
    asset2 = _asset(amm_snapshot.get("asset2") if isinstance(amm_snapshot.get("asset2"), Mapping) else {})
    reserve1 = _non_negative(amm_snapshot.get("reserve1", 0.0))
    reserve2 = _non_negative(amm_snapshot.get("reserve2", 0.0))
    fee = _fee(amm_snapshot.get("trading_fee", 0.0))

    if requested_size <= 0.0 or reserve1 <= 0.0 or reserve2 <= 0.0:
        return _amm_unavailable(["AMM_MALFORMED"])
    if source == asset1 and destination == asset2:
        reserve_in, reserve_out = reserve1, reserve2
    elif source == asset2 and destination == asset1:
        reserve_in, reserve_out = reserve2, reserve1
    else:
        return _amm_unavailable(["AMM_PAIR_MISMATCH"])

    input_after_fee = requested_size * (1.0 - fee)
    if input_after_fee <= 0.0:
        return _amm_unavailable(["AMM_FEE_TOO_HIGH"])
    output = (reserve_out * input_after_fee) / (reserve_in + input_after_fee)
    spot_price = reserve_out / reserve_in
    effective_price = output / requested_size if requested_size > 0.0 else 0.0
    price_impact = _unit(max(0.0, (spot_price - effective_price) / max(spot_price, 1e-12)))
    ideal_output = requested_size * spot_price
    fill_ratio = _unit(output / max(ideal_output, 1e-12))
    reserve_depth_factor = _unit(reserve_in / max(requested_size * 20.0, 1e-12))
    imbalance = abs(reserve1 - reserve2) / max(reserve1 + reserve2, 1e-12)
    liquidity_stability_factor = _unit((0.70 * reserve_depth_factor) + (0.30 * (1.0 - _unit(imbalance))))
    score = _unit((1.0 - price_impact) * liquidity_stability_factor)
    warnings: list[str] = []
    if price_impact > AMM_HARD_IMPACT_THRESHOLD:
        warnings.append("AMM_PRICE_IMPACT_TOO_HIGH")
    elif price_impact > AMM_MARGINAL_IMPACT_THRESHOLD:
        warnings.append("AMM_PRICE_IMPACT_ELEVATED")
    if reserve_depth_factor < 0.5:
        warnings.append("AMM_SHALLOW_RESERVES")
    if imbalance > 0.75:
        warnings.append("AMM_EXTREME_IMBALANCE")
    return {
        "available": price_impact <= AMM_HARD_IMPACT_THRESHOLD and score > 0.0,
        "score": _round(score),
        "price_impact": _round(price_impact),
        "fill_ratio": _round(fill_ratio),
        "effective_price": _round(effective_price),
        "warnings": warnings,
    }


def _amm_unavailable(warnings: list[str]) -> dict[str, object]:
    return {
        "available": False,
        "score": 0.0,
        "price_impact": 1.0,
        "fill_ratio": 0.0,
        "effective_price": 0.0,
        "warnings": warnings,
    }


def _liquidity_source(orderbook_available: bool, amm_available: bool) -> str:
    if orderbook_available and amm_available:
        return "hybrid"
    if orderbook_available:
        return "orderbook"
    if amm_available:
        return "amm"
    return "unknown"


def _preferred_source(
    *,
    orderbook_available: bool,
    amm_available: bool,
    orderbook_score: float,
    amm_score: float,
    orderbook_impact: float,
    amm_impact: float,
    orderbook_fill: float,
    amm_fill: float,
) -> str:
    if not orderbook_available and not amm_available:
        return "unknown"
    if orderbook_available and not amm_available:
        return "orderbook"
    if amm_available and not orderbook_available:
        return "amm"
    orderbook_rank = (orderbook_impact, -orderbook_fill, -orderbook_score, "orderbook")
    amm_rank = (amm_impact, -amm_fill, -amm_score, "amm")
    return "orderbook" if orderbook_rank <= amm_rank else "amm"


def _preferred_metrics(
    *,
    preferred_source: str,
    orderbook_impact: float,
    amm_impact: float,
    orderbook_fill: float,
    amm_fill: float,
) -> tuple[float, float]:
    if preferred_source == "orderbook":
        return orderbook_impact, orderbook_fill
    if preferred_source == "amm":
        return amm_impact, amm_fill
    return 1.0, 0.0


def _decision(
    *,
    malformed: bool,
    source: str,
    expected_fill_ratio: float,
    expected_price_impact: float,
    orderbook_available: bool,
    amm_available: bool,
) -> tuple[str, str | None]:
    if malformed:
        return "avoid", "malformed_input"
    if source == "unknown" or (not orderbook_available and not amm_available):
        return "avoid", "no_viable_liquidity_source"
    if expected_fill_ratio <= 0.0:
        return "avoid", "expected_fill_ratio_zero"
    if expected_price_impact > AMM_HARD_IMPACT_THRESHOLD:
        return "avoid", "price_impact_too_high"
    if expected_fill_ratio >= 0.80 and expected_price_impact <= AMM_MARGINAL_IMPACT_THRESHOLD:
        return "usable", None
    return "marginal", None


def _asset(raw: object) -> dict[str, object]:
    data = raw if isinstance(raw, Mapping) else {}
    currency = str(data.get("currency", "") or "").strip().upper()
    issuer = data.get("issuer")
    parsed_issuer = None if issuer is None else str(issuer).strip() or None
    if currency == "XRP":
        parsed_issuer = None
    return {"currency": currency, "issuer": parsed_issuer}


def _fee(raw: object) -> float:
    value = _non_negative(raw)
    if value > 1.0:
        value = value / 100_000.0
    return min(value, 0.10)


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


def _round(value: object, digits: int = 6) -> float:
    parsed = _finite(value)
    rounded = round(parsed, digits)
    return 0.0 if rounded == -0.0 else rounded


__all__ = [
    "LIQUIDITY_SOURCE_SCHEMA_VERSION",
    "XRPL_LIQUIDITY_SOURCE_WARNING",
    "evaluate_liquidity_sources",
]
