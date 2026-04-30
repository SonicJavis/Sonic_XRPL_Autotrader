"""Deterministic XRPL routing feasibility model built from normalized books.

The model is advisory-only. It does not call XRPL pathfinding endpoints, build
transactions, or infer liquidity beyond the supplied funded orderbook snapshots.
"""

from __future__ import annotations

from math import isfinite, sqrt
from typing import Any, Iterable, Mapping


XRPL_PATHFINDING_WARNING = (
    "Pathfinding model uses funded snapshot orderbooks only; routing remains uncertain and non-executable"
)
SLIPPAGE_FAILURE_THRESHOLD = 0.15
FRAGMENTATION_FAILURE_THRESHOLD = 0.75
FRAGILITY_SIZE_DELTA = 0.05


Asset = tuple[str, str | None]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if not isfinite(parsed):
        return default
    return parsed


def _round_float(value: float, digits: int = 12) -> float:
    if not isfinite(value):
        return 0.0
    rounded = round(value, digits)
    if rounded == -0.0:
        return 0.0
    return rounded


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    if not isfinite(value):
        return lower
    return max(lower, min(value, upper))


def _asset(currency: str | Mapping[str, Any], issuer: str | None = None) -> Asset:
    if isinstance(currency, Mapping):
        return (str(currency.get("currency", "")).strip().upper(), _issuer(currency.get("issuer")))
    normalized = str(currency).strip().upper()
    return (normalized, None if normalized == "XRP" else _issuer(issuer))


def _issuer(value: Any) -> str | None:
    if value is None:
        return None
    parsed = str(value).strip()
    return parsed or None


def _offer_assets(offer: Mapping[str, Any]) -> tuple[Asset, Asset]:
    source = _asset(str(offer.get("currency_gets", "")), _issuer(offer.get("issuer_gets")))
    destination = _asset(str(offer.get("currency_pays", "")), _issuer(offer.get("issuer_pays")))
    return source, destination


def _book_matches(book: Mapping[str, Any], source: Asset, destination: Asset) -> bool:
    offers = book.get("offers")
    if not isinstance(offers, list) or not offers:
        return False
    first = offers[0]
    if not isinstance(first, Mapping):
        return False
    return _offer_assets(first) == (source, destination)


def _find_book(orderbooks: Iterable[Mapping[str, Any]] | Mapping[Any, Mapping[str, Any]], source: Asset, destination: Asset) -> Mapping[str, Any] | None:
    values: Iterable[Mapping[str, Any]]
    if isinstance(orderbooks, Mapping):
        values = [book for book in orderbooks.values() if isinstance(book, Mapping)]
    else:
        values = orderbooks

    for book in values:
        if isinstance(book, Mapping) and _book_matches(book, source, destination):
            return book
    return None


def _simulate_hop(book: Mapping[str, Any] | None, input_size: float) -> dict[str, Any]:
    requested = max(0.0, _safe_float(input_size))
    if book is None or requested <= 0.0:
        return _empty_hop(requested)

    offers = [offer for offer in book.get("offers", []) if isinstance(offer, Mapping)]
    if not offers:
        return _empty_hop(requested)

    capacity = sum(max(0.0, _safe_float(offer.get("effective_gets"))) for offer in offers)
    best_price = max(0.0, _safe_float(offers[0].get("quality")))
    remaining = requested
    filled_input = 0.0
    output = 0.0
    levels_consumed = 0

    for offer in offers:
        available_input = max(0.0, _safe_float(offer.get("effective_gets")))
        available_output = max(0.0, _safe_float(offer.get("effective_pays")))
        if available_input <= 0.0 or available_output <= 0.0 or remaining <= 0.0:
            continue
        consumed = min(available_input, remaining)
        output += available_output * (consumed / available_input)
        filled_input += consumed
        remaining -= consumed
        levels_consumed += 1
        if remaining <= 0.0:
            break

    fill_ratio = _clamp(filled_input / requested if requested > 0.0 else 0.0)
    effective_price = output / filled_input if filled_input > 0.0 else 0.0
    slippage = abs(effective_price - best_price) / best_price if best_price > 0.0 and filled_input > 0.0 else 1.0
    fragmentation = _fragmentation_score(offers, levels_consumed, requested)

    return {
        "requested_size": _round_float(requested),
        "filled_input": _round_float(filled_input),
        "output_size": _round_float(output),
        "capacity": _round_float(capacity),
        "fill_ratio": _round_float(fill_ratio),
        "effective_price": _round_float(effective_price),
        "slippage": _round_float(_clamp(slippage)),
        "levels_consumed": int(levels_consumed),
        "fragmentation_score": _round_float(fragmentation),
    }


def _empty_hop(requested: float) -> dict[str, Any]:
    return {
        "requested_size": _round_float(requested),
        "filled_input": 0.0,
        "output_size": 0.0,
        "capacity": 0.0,
        "fill_ratio": 0.0,
        "effective_price": 0.0,
        "slippage": 1.0,
        "levels_consumed": 0,
        "fragmentation_score": 1.0,
    }


def _fragmentation_score(offers: list[Mapping[str, Any]], levels_consumed: int, requested_size: float) -> float:
    if not offers:
        return 1.0
    depths = [max(0.0, _safe_float(offer.get("effective_gets"))) for offer in offers]
    nonzero_depths = [depth for depth in depths if depth > 0.0]
    if not nonzero_depths:
        return 1.0

    used_level_ratio = _clamp(levels_consumed / max(1, len(nonzero_depths)))
    mean_depth = sum(nonzero_depths) / len(nonzero_depths)
    variance = sum((depth - mean_depth) ** 2 for depth in nonzero_depths) / len(nonzero_depths)
    uneven_depth = _clamp((sqrt(variance) / mean_depth) if mean_depth > 0.0 else 1.0)

    qualities = [max(0.0, _safe_float(offer.get("quality"))) for offer in offers if _safe_float(offer.get("quality")) > 0.0]
    quality_gaps: list[float] = []
    for prev, current in zip(qualities, qualities[1:]):
        quality_gaps.append((current - prev) / prev if prev > 0.0 and current >= prev else 0.0)
    gap_score = _clamp(max(quality_gaps) if quality_gaps else 0.0)

    size_pressure = _clamp(requested_size / max(sum(nonzero_depths), 1e-12))
    return _clamp((0.35 * used_level_ratio) + (0.30 * uneven_depth) + (0.20 * gap_score) + (0.15 * size_pressure))


def _path_fragility(book: Mapping[str, Any] | None, requested_size: float) -> float:
    base = _simulate_hop(book, requested_size)
    stressed = _simulate_hop(book, requested_size * (1.0 + FRAGILITY_SIZE_DELTA))
    return _clamp(float(base["fill_ratio"]) - float(stressed["fill_ratio"]))


def _evaluate_path(
    label: str,
    books: list[Mapping[str, Any]],
    requested_size: float,
) -> dict[str, Any]:
    hop_results: list[dict[str, Any]] = []
    next_input = requested_size

    for book in books:
        result = _simulate_hop(book, next_input)
        hop_results.append(result)
        next_input = float(result["output_size"])
        if next_input <= 0.0:
            break

    missing_hops = max(0, len(books) - len(hop_results))
    for _ in range(missing_hops):
        hop_results.append(_empty_hop(0.0))

    capacities = [float(result["capacity"]) for result in hop_results]
    fill_ratios = [float(result["fill_ratio"]) for result in hop_results]
    path_capacity = min(capacities) if capacities else 0.0
    weakest_fill_ratio = min(fill_ratios) if fill_ratios else 0.0
    total_slippage = sum(float(result["slippage"]) for result in hop_results)
    fragmentation = max((float(result["fragmentation_score"]) for result in hop_results), default=1.0)
    fragility = max((_path_fragility(book, requested_size) for book in books), default=1.0)
    hop_count = len(books)

    capacity_score = _clamp(path_capacity / max(requested_size, 1e-12))
    slippage_penalty = _clamp(total_slippage / SLIPPAGE_FAILURE_THRESHOLD)
    hop_penalty = _clamp((hop_count - 1) * 0.18)
    viability = _clamp(
        (0.48 * weakest_fill_ratio)
        + (0.22 * capacity_score)
        + (0.12 * (1.0 - fragmentation))
        + (0.10 * (1.0 - fragility))
        + (0.08 * (1.0 - slippage_penalty))
        - hop_penalty
    )
    uncertainty = _clamp(
        (0.25 * hop_penalty)
        + (0.25 * fragmentation)
        + (0.25 * fragility)
        + (0.25 * (1.0 - capacity_score))
        + (0.10 * slippage_penalty)
    )

    return {
        "label": label,
        "hop_count": hop_count,
        "hop_results": hop_results,
        "path_capacity": _round_float(path_capacity),
        "estimated_slippage": _round_float(total_slippage),
        "path_viability_score": _round_float(viability),
        "uncertainty_score": _round_float(uncertainty),
        "liquidity_fragmentation_score": _round_float(fragmentation),
        "liquidity_fragility_score": _round_float(fragility),
    }


def evaluate_pathfinding_uncertainty(
    normalized_orderbooks: Iterable[Mapping[str, Any]] | Mapping[Any, Mapping[str, Any]],
    source_asset: str | Mapping[str, Any],
    destination_asset: str | Mapping[str, Any],
    trade_size: float,
    *,
    bridge_asset: str | Mapping[str, Any] = "XRP",
    intermediate_assets: Iterable[str | Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Evaluate direct, XRP-bridge, and explicitly provided two-hop paths."""

    source = _asset(source_asset)
    destination = _asset(destination_asset)
    bridge = _asset(bridge_asset)
    requested_size = max(0.0, _safe_float(trade_size))

    direct_book = _find_book(normalized_orderbooks, source, destination)
    bridge_first = _find_book(normalized_orderbooks, source, bridge)
    bridge_second = _find_book(normalized_orderbooks, bridge, destination)

    candidates: list[dict[str, Any]] = []
    direct_available = direct_book is not None
    bridge_available = bridge_first is not None and bridge_second is not None

    if direct_available:
        candidates.append(_evaluate_path("direct", [direct_book], requested_size))
    if bridge_available:
        candidates.append(_evaluate_path("xrp_bridge", [bridge_first, bridge_second], requested_size))

    multi_hop_possible = False
    for raw_intermediate in intermediate_assets or []:
        intermediate = _asset(raw_intermediate)
        if intermediate in {source, destination, bridge}:
            continue
        first = _find_book(normalized_orderbooks, source, intermediate)
        second = _find_book(normalized_orderbooks, intermediate, destination)
        if first is not None and second is not None:
            multi_hop_possible = True
            candidates.append(_evaluate_path(f"multi_hop:{intermediate[0]}", [first, second], requested_size))

    best = max(candidates, key=lambda item: (item["path_viability_score"], -item["hop_count"], item["label"])) if candidates else None
    failure_modes = _failure_modes(
        requested_size=requested_size,
        direct_available=direct_available,
        bridge_available=bridge_available,
        multi_hop_possible=multi_hop_possible,
        best=best,
        candidates=candidates,
    )

    return {
        "path_required": bool(best is not None and best["hop_count"] > 1),
        "direct_liquidity_available": direct_available,
        "bridge_available": bridge_available,
        "multi_hop_possible": multi_hop_possible,
        "estimated_hops": int(best["hop_count"]) if best is not None else 0,
        "selected_path": str(best["label"]) if best is not None else "none",
        "path_capacity": _round_float(float(best["path_capacity"])) if best is not None else 0.0,
        "estimated_slippage": _round_float(float(best["estimated_slippage"])) if best is not None else 0.0,
        "path_viability_score": _round_float(float(best["path_viability_score"])) if best is not None else 0.0,
        "uncertainty_score": _round_float(float(best["uncertainty_score"])) if best is not None else 1.0,
        "liquidity_fragmentation_score": _round_float(float(best["liquidity_fragmentation_score"])) if best is not None else 1.0,
        "liquidity_fragility_score": _round_float(float(best["liquidity_fragility_score"])) if best is not None else 1.0,
        "failure_modes": sorted(set(failure_modes)),
        "candidate_paths": candidates,
        "is_shadow": True,
        "is_advisory": True,
        "is_executable": False,
        "is_truth": False,
        "xrpl_warning": XRPL_PATHFINDING_WARNING,
    }


def _failure_modes(
    *,
    requested_size: float,
    direct_available: bool,
    bridge_available: bool,
    multi_hop_possible: bool,
    best: Mapping[str, Any] | None,
    candidates: list[Mapping[str, Any]],
) -> list[str]:
    modes: list[str] = []
    if not direct_available:
        modes.append("NO_DIRECT_PATH")
    if not bridge_available:
        modes.append("NO_BRIDGE_PATH")
    if not multi_hop_possible:
        modes.append("NO_LIMITED_MULTI_HOP_PATH")
    if best is None:
        modes.append("NO_PATH_AVAILABLE")
        return modes

    if float(best["path_capacity"]) < requested_size:
        modes.append("INSUFFICIENT_CAPACITY_FOR_SIZE")
    hop_capacities = [
        float(result["capacity"])
        for candidate in candidates
        for result in candidate.get("hop_results", [])
        if isinstance(result, Mapping)
    ]
    if hop_capacities and min(hop_capacities) < max(hop_capacities) * 0.5:
        modes.append("WEAKEST_HOP_BOTTLENECK")
    if float(best["estimated_slippage"]) > SLIPPAGE_FAILURE_THRESHOLD:
        modes.append("EXTREME_SLIPPAGE")
    if float(best["liquidity_fragmentation_score"]) > FRAGMENTATION_FAILURE_THRESHOLD:
        modes.append("HIGHLY_FRAGMENTED_LIQUIDITY")
    if _asymmetric_hops(best):
        modes.append("ASYMMETRIC_LIQUIDITY_ACROSS_HOPS")
    return modes


def _asymmetric_hops(candidate: Mapping[str, Any]) -> bool:
    hop_results = [result for result in candidate.get("hop_results", []) if isinstance(result, Mapping)]
    if len(hop_results) < 2:
        return False
    capacities = [float(result["capacity"]) for result in hop_results]
    if not capacities or max(capacities) <= 0.0:
        return False
    return min(capacities) / max(capacities) < 0.5


__all__ = [
    "XRPL_PATHFINDING_WARNING",
    "evaluate_pathfinding_uncertainty",
]
