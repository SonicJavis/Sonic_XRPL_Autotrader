from __future__ import annotations

from math import exp, isfinite
from typing import Mapping


LIQUIDITY_DECAY_SCHEMA_VERSION = "1.0"
XRPL_LIQUIDITY_DECAY_WARNING = (
    "XRPL liquidity freshness is ledger-based; decay is advisory, shadow-only, and non-executing"
)


def evaluate_liquidity_decay(
    *,
    snapshot_ledger_index: int,
    snapshot_ledger_time: int | None,
    current_ledger_index: int,
    current_ledger_time: int | None,
    processing_time: float | None,
    execution_feasibility: Mapping[str, object] | None,
    liquidity_source_model: Mapping[str, object] | None,
    recent_gap_count: int = 0,
    recent_duplicate_count: int = 0,
    recent_latency_ms: float | None = None,
) -> dict[str, object]:
    warnings: list[str] = []
    feasibility = dict(execution_feasibility or {})
    liquidity = dict(liquidity_source_model or {})
    gap_count = max(0, int(_finite(recent_gap_count)))
    duplicate_count = max(0, int(_finite(recent_duplicate_count)))
    latency_ms = _non_negative(recent_latency_ms) if recent_latency_ms is not None else None
    processing = _non_negative(processing_time) if processing_time is not None else None

    if not feasibility or not liquidity:
        return _invalid("missing_decay_context", warnings)
    if "execution_feasibility_score" not in feasibility or "expected_fill_ratio" not in liquidity:
        return _invalid("missing_required_fields", warnings)

    snapshot_ledger = int(_finite(snapshot_ledger_index, default=-1.0))
    current_ledger = int(_finite(current_ledger_index, default=-1.0))
    if snapshot_ledger < 0 or current_ledger < 0:
        return _invalid("invalid_ledger_index", warnings)
    age_ledgers = current_ledger - snapshot_ledger
    if age_ledgers < 0:
        return _invalid("negative_ledger_age", ["snapshot ledger is ahead of current ledger"])

    age_seconds: float | None = None
    if snapshot_ledger_time is not None and current_ledger_time is not None:
        age_seconds = _finite(current_ledger_time) - _finite(snapshot_ledger_time)
        if age_seconds < 0.0:
            warnings.append("ledger time moved backward; diagnostics only")
            age_seconds = 0.0

    feasibility_score = _unit(feasibility.get("execution_feasibility_score", 0.0))
    fill_ratio = _unit(liquidity.get("expected_fill_ratio", feasibility.get("expected_fill_ratio", 0.0)))
    decay_factor = exp(-0.12 * max(0, age_ledgers))

    if _uses_amm(liquidity):
        decay_factor *= 0.85
        warnings.append("AMM-linked liquidity decays faster between ledgers")
    if gap_count > 0:
        decay_factor *= max(0.0, 1.0 - min(0.75, gap_count * 0.25))
        warnings.append("recent ledger gap reduces liquidity freshness")
    if latency_ms is not None and latency_ms > 3000.0:
        decay_factor *= max(0.0, 1.0 - min(0.50, (latency_ms - 3000.0) / 12000.0))
        warnings.append("high ingestion latency reduces freshness confidence")
    if duplicate_count > 0:
        warnings.append("duplicate ledger events observed; diagnostics only")
    if processing is not None and processing > 0.0:
        warnings.append("processing time is diagnostic only")

    decay_factor = _unit(decay_factor)
    staleness_score = _unit(1.0 - decay_factor)
    decayed_feasibility = _unit(feasibility_score * decay_factor)
    decayed_fill = _unit(fill_ratio * decay_factor)

    decision = "fresh"
    stale = False
    if gap_count >= 3:
        decision = "invalid"
        stale = True
        warnings.append("excessive ledger gaps invalidate snapshot assumptions")
        decay_factor = 0.0
        staleness_score = 1.0
        decayed_feasibility = 0.0
        decayed_fill = 0.0
    elif age_ledgers > 12:
        decision = "invalid"
        stale = True
        warnings.append("snapshot age exceeds ledger validity limit")
        decay_factor = 0.0
        staleness_score = 1.0
        decayed_feasibility = 0.0
        decayed_fill = 0.0
    elif age_ledgers > 8 or decay_factor < 0.20 or (_uses_amm(liquidity) and gap_count > 0 and latency_ms is not None and latency_ms > 3000.0):
        decision = "stale"
        stale = True
        warnings.append("snapshot liquidity is stale under ledger-based decay")
    elif age_ledgers >= 2 or decay_factor <= 0.85 or gap_count > 0 or (latency_ms is not None and latency_ms > 3000.0):
        decision = "degraded"
        warnings.append("snapshot liquidity is degraded by ledger progression")

    if age_ledgers == 0 and not warnings:
        warnings.append("snapshot is from current ledger")

    return _result(
        snapshot_age_ledgers=age_ledgers,
        snapshot_age_seconds=age_seconds,
        staleness_score=staleness_score,
        decay_factor=decay_factor,
        decayed_feasibility_score=decayed_feasibility,
        decayed_fill_confidence=decayed_fill,
        stale=stale,
        decision=decision,
        warnings=warnings,
    )


def _uses_amm(liquidity: Mapping[str, object]) -> bool:
    return (
        str(liquidity.get("liquidity_source", "")).lower() in {"amm", "hybrid"}
        or str(liquidity.get("preferred_source", "")).lower() == "amm"
        or bool(liquidity.get("amm_available", False))
    )


def _invalid(reason: str, warnings: list[str]) -> dict[str, object]:
    return _result(
        snapshot_age_ledgers=0,
        snapshot_age_seconds=None,
        staleness_score=1.0,
        decay_factor=0.0,
        decayed_feasibility_score=0.0,
        decayed_fill_confidence=0.0,
        stale=True,
        decision="invalid",
        warnings=[*warnings, reason],
    )


def _result(
    *,
    snapshot_age_ledgers: int,
    snapshot_age_seconds: float | None,
    staleness_score: float,
    decay_factor: float,
    decayed_feasibility_score: float,
    decayed_fill_confidence: float,
    stale: bool,
    decision: str,
    warnings: list[str],
) -> dict[str, object]:
    return {
        "schema_version": LIQUIDITY_DECAY_SCHEMA_VERSION,
        "snapshot_age_ledgers": max(0, int(snapshot_age_ledgers)),
        "snapshot_age_seconds": None if snapshot_age_seconds is None else round(_non_negative(snapshot_age_seconds), 6),
        "staleness_score": round(_unit(staleness_score), 6),
        "decay_factor": round(_unit(decay_factor), 6),
        "decayed_feasibility_score": round(_unit(decayed_feasibility_score), 6),
        "decayed_fill_confidence": round(_unit(decayed_fill_confidence), 6),
        "stale": bool(stale),
        "decision": decision if decision in {"fresh", "degraded", "stale", "invalid"} else "invalid",
        "warnings": sorted({str(warning) for warning in warnings if str(warning)}),
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
