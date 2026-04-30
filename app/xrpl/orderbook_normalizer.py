"""Deterministic XRPL ``book_offers`` normalization.

This module is read-only and performs no transaction construction. It converts
XRPL offer payload variants into funded, quality-sorted levels suitable for
paper-only scoring and simulation.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any, Iterable, Mapping


DROPS_PER_XRP = 1_000_000.0
FLOAT_TOLERANCE = 1e-9
XRPL_ORDERBOOK_WARNING = (
    "book_offers normalization is read-only and snapshot-based; visible liquidity remains non-executable"
)


@dataclass(frozen=True)
class XRPLAmount:
    value: float
    currency: str
    issuer: str | None
    is_xrp: bool


def _safe_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not isfinite(parsed):
        return None
    return parsed


def _non_negative(value: float | None) -> float | None:
    if value is None or value < 0.0:
        return None
    return value


def _round_float(value: float, digits: int = 12) -> float:
    if not isfinite(value):
        return 0.0
    rounded = round(value, digits)
    if rounded == -0.0:
        return 0.0
    return rounded


def _parse_xrp_drops(raw: Any) -> float | None:
    drops = _non_negative(_safe_float(raw))
    if drops is None:
        return None
    return drops / DROPS_PER_XRP


def _parse_iou_value(raw: Any) -> float | None:
    return _non_negative(_safe_float(raw))


def _parse_amount(raw: Any) -> XRPLAmount | None:
    if isinstance(raw, str):
        value = _parse_xrp_drops(raw)
        if value is None:
            return None
        return XRPLAmount(value=value, currency="XRP", issuer=None, is_xrp=True)

    if isinstance(raw, Mapping):
        currency = raw.get("currency")
        issuer = raw.get("issuer")
        value = _parse_iou_value(raw.get("value"))
        if not isinstance(currency, str) or not currency.strip():
            return None
        if not isinstance(issuer, str) or not issuer.strip():
            return None
        if value is None:
            return None
        return XRPLAmount(value=value, currency=currency, issuer=issuer, is_xrp=False)

    return None


def _parse_funded_amount(raw: Any, reference: XRPLAmount) -> float | None:
    if raw is None:
        return None

    if isinstance(raw, Mapping):
        parsed = _parse_amount(raw)
        if parsed is None:
            return None
        if parsed.currency != reference.currency or parsed.issuer != reference.issuer:
            return None
        return parsed.value

    if reference.is_xrp:
        return _parse_xrp_drops(raw)
    return _parse_iou_value(raw)


def _clamp(value: float, lower: float, upper: float) -> float:
    if not isfinite(value):
        return lower
    return max(lower, min(value, upper))


def _get_offer_field(offer: Mapping[str, Any], primary: str, fallback: str) -> Any:
    if primary in offer:
        return offer[primary]
    return offer.get(fallback)


def normalize_offer(offer: Mapping[str, Any]) -> dict[str, Any] | None:
    """Normalize one XRPL ``book_offers`` offer.

    Malformed, zero-size, or effectively unfunded offers return ``None``.
    """

    taker_gets = _parse_amount(_get_offer_field(offer, "TakerGets", "taker_gets"))
    taker_pays = _parse_amount(_get_offer_field(offer, "TakerPays", "taker_pays"))
    if taker_gets is None or taker_pays is None:
        return None
    if taker_gets.value <= 0.0 or taker_pays.value <= 0.0:
        return None

    quality = taker_pays.value / taker_gets.value
    if not isfinite(quality) or quality <= 0.0:
        return None

    raw_quality = _safe_float(offer.get("quality"))
    quality_delta = abs(raw_quality - quality) if raw_quality is not None else None
    quality_matches = quality_delta is None or quality_delta <= FLOAT_TOLERANCE

    if "taker_gets_funded" in offer:
        funded_gets = _parse_funded_amount(offer.get("taker_gets_funded"), taker_gets)
        effective_gets = funded_gets if funded_gets is not None else 0.0
    elif "owner_funds" in offer:
        owner_funds = _parse_funded_amount(offer.get("owner_funds"), taker_gets)
        effective_gets = min(taker_gets.value, owner_funds if owner_funds is not None else 0.0)
    else:
        effective_gets = taker_gets.value

    effective_gets = _clamp(effective_gets, 0.0, taker_gets.value)
    effective_pays = effective_gets * quality

    if "taker_pays_funded" in offer:
        funded_pays = _parse_funded_amount(offer.get("taker_pays_funded"), taker_pays)
        if funded_pays is None:
            effective_gets = 0.0
            effective_pays = 0.0
        else:
            effective_pays = min(effective_pays, _clamp(funded_pays, 0.0, taker_pays.value))
            effective_gets = min(effective_gets, effective_pays / quality)

    if effective_gets <= 0.0 or effective_pays <= 0.0:
        return None

    return {
        "taker_gets": _round_float(taker_gets.value),
        "taker_pays": _round_float(taker_pays.value),
        "effective_gets": _round_float(effective_gets),
        "effective_pays": _round_float(effective_pays),
        "currency_gets": taker_gets.currency,
        "currency_pays": taker_pays.currency,
        "issuer_gets": taker_gets.issuer,
        "issuer_pays": taker_pays.issuer,
        "is_xrp_gets": taker_gets.is_xrp,
        "is_xrp_pays": taker_pays.is_xrp,
        "quality": _round_float(quality, digits=15),
        "quality_delta": _round_float(quality_delta, digits=15) if quality_delta is not None else None,
        "quality_matches": quality_matches,
        "owner": str(offer.get("owner") or offer.get("Account") or ""),
        "funded": True,
    }


def _quality_key(quality: float) -> str:
    return format(_round_float(quality, digits=15), ".15g")


def _build_book(normalized_offers: list[dict[str, Any]], spread_estimate: float | None = None) -> dict[str, Any]:
    cumulative_depth: list[float] = []
    depth_by_quality: dict[str, float] = {}
    running_depth = 0.0

    for normalized in normalized_offers:
        running_depth += float(normalized["effective_gets"])
        cumulative_depth.append(_round_float(running_depth))
        quality_key = _quality_key(float(normalized["quality"]))
        depth_by_quality[quality_key] = _round_float(
            depth_by_quality.get(quality_key, 0.0) + float(normalized["effective_gets"])
        )

    finite_spread = _safe_float(spread_estimate)
    if finite_spread is not None and finite_spread < 0.0:
        finite_spread = None

    return {
        "offers": normalized_offers,
        "offer_count": len(normalized_offers),
        "cumulative_depth": cumulative_depth,
        "depth_by_quality": dict(sorted(depth_by_quality.items(), key=lambda item: float(item[0]))),
        "best_price": normalized_offers[0]["quality"] if normalized_offers else None,
        "spread_estimate": _round_float(finite_spread) if finite_spread is not None else None,
        "is_shadow": True,
        "is_advisory": True,
        "is_executable": False,
        "is_truth": False,
        "xrpl_warning": XRPL_ORDERBOOK_WARNING,
    }


def normalize_book_offers(
    offers: Iterable[Mapping[str, Any]],
    *,
    spread_estimate: float | None = None,
) -> dict[str, Any]:
    """Normalize and quality-sort one side of an XRPL order book.

    Sorting is stable, preserving FIFO order for offers with identical
    recomputed quality.
    """

    normalized = [item for item in (normalize_offer(offer) for offer in offers) if item is not None]
    sorted_offers = sorted(normalized, key=lambda item: float(item["quality"]))
    return _build_book(sorted_offers, spread_estimate=spread_estimate)


__all__ = [
    "DROPS_PER_XRP",
    "XRPL_ORDERBOOK_WARNING",
    "normalize_offer",
    "normalize_book_offers",
]
