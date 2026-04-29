from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from math import isfinite
from typing import Iterable, Mapping


ORDER_INTENT_SCHEMA_VERSION = "1.0"
XRPL_ORDER_INTENT_WARNING = (
    "Order intents are simulated from validated ledger snapshots only; estimates are advisory and non-executing"
)


@dataclass(frozen=True, slots=True)
class XRPLIntentSnapshot:
    token_id: int
    issuer: str
    currency: str
    ledger_index: int
    ledger_time: datetime
    best_bid: float
    best_ask: float
    bid_depth_xrp: float
    ask_depth_xrp: float
    spread_pct: float
    validated: bool = True
    recent_ledger_gap: bool = False
    snapshot_complete: bool = True

    @staticmethod
    def from_row(row: object, *, issuer: str = "", currency: str = "", recent_ledger_gap: bool = False) -> "XRPLIntentSnapshot":
        observed_at = getattr(row, "observed_at", None)
        if isinstance(observed_at, datetime):
            ledger_time = observed_at
        else:
            ledger_time = datetime.fromtimestamp(0, tz=timezone.utc)
        return XRPLIntentSnapshot(
            token_id=max(0, int(_finite(getattr(row, "token_id", 0)))),
            issuer=str(issuer or getattr(row, "issuer", "") or ""),
            currency=str(currency or getattr(row, "currency", "") or ""),
            ledger_index=max(0, int(_finite(getattr(row, "ledger_index", 0)))),
            ledger_time=_utc(ledger_time),
            best_bid=_non_negative(getattr(row, "best_bid", 0.0)),
            best_ask=_non_negative(getattr(row, "best_ask", 0.0)),
            bid_depth_xrp=_non_negative(getattr(row, "bid_depth_xrp", 0.0)),
            ask_depth_xrp=_non_negative(getattr(row, "ask_depth_xrp", 0.0)),
            spread_pct=_non_negative(getattr(row, "spread_pct", 0.0)),
            validated=True,
            recent_ledger_gap=recent_ledger_gap,
            snapshot_complete=True,
        )


@dataclass(frozen=True, slots=True)
class XRPLOrderIntent:
    intent_id: str
    schema_version: str
    source_recommendation_id: str
    action: str
    token_id: str
    issuer: str
    proposed_size: float
    size_basis: str
    confidence: float
    predicted_regime: str
    attribution: dict[str, object]
    constraints: dict[str, object]
    xrpl_context: dict[str, object]
    execution_estimates: dict[str, object]
    pathfinding: dict[str, object]
    fill_model: dict[str, object]
    is_shadow: bool = True
    is_advisory: bool = True
    is_executable: bool = False
    is_truth: bool = False

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["schema_version"] = ORDER_INTENT_SCHEMA_VERSION
        data["intent_id"] = compute_intent_id(data)
        data["proposed_size"] = round(_non_negative(data["proposed_size"]), 6)
        data["confidence"] = round(_unit(data["confidence"]), 6)
        data["is_shadow"] = True
        data["is_advisory"] = True
        data["is_executable"] = False
        data["is_truth"] = False
        data["constraints"] = _sanitize_mapping(data["constraints"])
        data["xrpl_context"] = _sanitize_mapping(data["xrpl_context"])
        data["execution_estimates"] = _sanitize_mapping(data["execution_estimates"])
        data["pathfinding"] = _sanitize_mapping(data["pathfinding"])
        data["fill_model"] = _sanitize_mapping(data["fill_model"])
        return {key: data[key] for key in sorted(data)}


def build_order_intent(
    *,
    recommendation: Mapping[str, object],
    snapshot: XRPLIntentSnapshot,
    requested_size: float = 100.0,
    liquidity_threshold: float = 0.20,
    path_threshold: float = 0.35,
) -> XRPLOrderIntent:
    scope = recommendation.get("scope") if isinstance(recommendation.get("scope"), Mapping) else {}
    scope_map = dict(scope)
    source_id = str(recommendation.get("recommendation_id", ""))
    attribution_name = str(scope_map.get("attribution", "unknown") or "unknown")
    predicted_regime = str(scope_map.get("regime", "UNKNOWN") or "UNKNOWN")
    requested = _non_negative(requested_size, default=100.0)
    depth = min(snapshot.bid_depth_xrp, snapshot.ask_depth_xrp)
    spread_penalty = _unit(snapshot.spread_pct / 20.0)
    liquidity_score = _unit((depth / max(requested, 1e-9)) * (1.0 - spread_penalty))
    path_required = attribution_name == "path_instability" or snapshot.spread_pct >= 5.0
    path_viability = _unit(1.0 - (0.35 if path_required else 0.0) - spread_penalty)
    estimated_slippage = round(_non_negative(snapshot.spread_pct / 100.0), 6)
    depth_at_size = min(depth, requested)
    expected_fill_ratio = min(0.95, _unit((depth_at_size / max(requested, 1e-9)) * liquidity_score * path_viability))
    confidence = _unit(
        _unit(recommendation.get("stability_score", 0.0))
        * _unit(recommendation.get("consistency_score", 0.0))
        * liquidity_score
        * path_viability
    )
    proposed_size = min(requested, depth_at_size) * max(0.0, min(0.50, confidence))
    incomplete = (
        not snapshot.validated
        or not snapshot.snapshot_complete
        or snapshot.ledger_index <= 0
        or depth <= 0.0
        or snapshot.best_ask <= 0.0
        or snapshot.recent_ledger_gap
    )
    action = "buy"
    if (
        incomplete
        or liquidity_score < liquidity_threshold
        or path_viability < path_threshold
        or proposed_size <= 0.0
    ):
        action = "avoid"
        proposed_size = 0.0
        confidence = min(confidence, 0.25)

    min_fill_ratio = _unit(expected_fill_ratio * max(0.0, 1.0 - spread_penalty - (0.20 if path_required else 0.0)))
    max_fill_ratio = min(0.95, max(min_fill_ratio, _unit(expected_fill_ratio + liquidity_score * 0.20)))
    confidence_adjusted_fill = _unit(expected_fill_ratio * confidence)
    intent = XRPLOrderIntent(
        intent_id="",
        schema_version=ORDER_INTENT_SCHEMA_VERSION,
        source_recommendation_id=source_id,
        action=action,
        token_id=str(snapshot.token_id),
        issuer=snapshot.issuer,
        proposed_size=proposed_size,
        size_basis="risk_capped" if action == "avoid" else "liquidity_fraction",
        confidence=confidence,
        predicted_regime=predicted_regime,
        attribution={
            "primary": attribution_name,
            "source_metric": str(recommendation.get("source_metric", "")),
            "support_size": max(0, int(_finite(recommendation.get("support_size", 0)))),
        },
        constraints={
            "max_slippage_bps": 500,
            "min_liquidity": round(max(0.0, requested * liquidity_threshold), 6),
            "max_position_fraction": 0.05,
        },
        xrpl_context={
            "ledger_index": int(snapshot.ledger_index),
            "ledger_time": int(_utc(snapshot.ledger_time).timestamp()),
            "validated": bool(snapshot.validated),
        },
        execution_estimates={
            "estimated_slippage": estimated_slippage,
            "liquidity_score": round(liquidity_score, 6),
            "depth_at_size": round(depth_at_size, 6),
            "expected_fill_ratio": round(expected_fill_ratio, 6),
        },
        pathfinding={
            "path_required": bool(path_required),
            "path_viability_score": round(path_viability, 6),
        },
        fill_model={
            "min_fill_ratio": round(min_fill_ratio, 6),
            "max_fill_ratio": round(max_fill_ratio, 6),
            "confidence_adjusted_fill": round(confidence_adjusted_fill, 6),
        },
    )
    return intent


def build_order_intents(
    *,
    recommendations: Iterable[Mapping[str, object]],
    snapshots_by_token: Mapping[int, XRPLIntentSnapshot],
    requested_size: float = 100.0,
    recent_ledger_gap: bool = False,
) -> list[XRPLOrderIntent]:
    rows: list[XRPLOrderIntent] = []
    seen: set[str] = set()
    for recommendation in recommendations:
        scope = recommendation.get("scope") if isinstance(recommendation.get("scope"), Mapping) else {}
        token_id = int(_finite(dict(scope).get("token_id", 0))) if isinstance(scope, Mapping) else 0
        snapshot = snapshots_by_token.get(token_id)
        if snapshot is None:
            continue
        if recent_ledger_gap and not snapshot.recent_ledger_gap:
            snapshot = XRPLIntentSnapshot(
                token_id=snapshot.token_id,
                issuer=snapshot.issuer,
                currency=snapshot.currency,
                ledger_index=snapshot.ledger_index,
                ledger_time=snapshot.ledger_time,
                best_bid=snapshot.best_bid,
                best_ask=snapshot.best_ask,
                bid_depth_xrp=snapshot.bid_depth_xrp,
                ask_depth_xrp=snapshot.ask_depth_xrp,
                spread_pct=snapshot.spread_pct,
                validated=snapshot.validated,
                recent_ledger_gap=True,
                snapshot_complete=snapshot.snapshot_complete,
            )
        intent = build_order_intent(recommendation=recommendation, snapshot=snapshot, requested_size=requested_size)
        intent_id = intent.to_dict()["intent_id"]
        if intent_id in seen:
            continue
        seen.add(str(intent_id))
        rows.append(intent)
    return sorted(rows, key=lambda row: _intent_sort_key(row.to_dict()))


def summarize_order_intents(intents: Iterable[XRPLOrderIntent]) -> dict[str, object]:
    rows = [intent.to_dict() for intent in intents]
    action_counts: dict[str, int] = {}
    for row in rows:
        action = str(row["action"])
        action_counts[action] = action_counts.get(action, 0) + 1
    avg_liquidity = _avg([row["execution_estimates"]["liquidity_score"] for row in rows])
    avg_fill = _avg([row["execution_estimates"]["expected_fill_ratio"] for row in rows])
    avg_path = _avg([row["pathfinding"]["path_viability_score"] for row in rows])
    return {
        "schema_version": ORDER_INTENT_SCHEMA_VERSION,
        "count": len(rows),
        "action_counts": dict(sorted(action_counts.items())),
        "avg_liquidity_score": round(avg_liquidity, 6),
        "avg_expected_fill_ratio": round(avg_fill, 6),
        "avg_path_viability_score": round(avg_path, 6),
        **_meta(),
    }


def compute_intent_id(data: Mapping[str, object]) -> str:
    context = data.get("xrpl_context") if isinstance(data.get("xrpl_context"), Mapping) else {}
    estimates = data.get("execution_estimates") if isinstance(data.get("execution_estimates"), Mapping) else {}
    pathfinding = data.get("pathfinding") if isinstance(data.get("pathfinding"), Mapping) else {}
    fill_model = data.get("fill_model") if isinstance(data.get("fill_model"), Mapping) else {}
    pattern = {
        "schema_version": str(data.get("schema_version", ORDER_INTENT_SCHEMA_VERSION)),
        "source_recommendation_id": str(data.get("source_recommendation_id", "")),
        "action": str(data.get("action", "")),
        "token_id": str(data.get("token_id", "")),
        "issuer": str(data.get("issuer", "")),
        "ledger_index": int(_finite(dict(context).get("ledger_index", 0))),
        "liquidity_score": round(_unit(dict(estimates).get("liquidity_score", 0.0)), 6),
        "expected_fill_ratio": round(_unit(dict(estimates).get("expected_fill_ratio", 0.0)), 6),
        "path_viability_score": round(_unit(dict(pathfinding).get("path_viability_score", 0.0)), 6),
        "confidence_adjusted_fill": round(_unit(dict(fill_model).get("confidence_adjusted_fill", 0.0)), 6),
    }
    encoded = json.dumps(pattern, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"intent_{sha256(encoded).hexdigest()[:24]}"


def _intent_sort_key(row: Mapping[str, object]) -> tuple[object, ...]:
    context = row.get("xrpl_context") if isinstance(row.get("xrpl_context"), Mapping) else {}
    return (
        -int(_finite(dict(context).get("ledger_index", 0))),
        str(row.get("token_id", "")),
        str(row.get("issuer", "")),
        str(row.get("source_recommendation_id", "")),
        str(row.get("intent_id", "")),
    )


def _sanitize_mapping(data: Mapping[str, object]) -> dict[str, object]:
    clean: dict[str, object] = {}
    for key, value in sorted(data.items()):
        if isinstance(value, bool):
            clean[str(key)] = value
        elif isinstance(value, int):
            clean[str(key)] = int(value)
        elif isinstance(value, float):
            clean[str(key)] = round(_finite(value), 6)
        else:
            clean[str(key)] = value
    return clean


def _avg(values: Iterable[object]) -> float:
    rows = [_finite(value) for value in values]
    return 0.0 if not rows else sum(rows) / len(rows)


def _utc(raw: datetime) -> datetime:
    value = raw if raw.tzinfo is not None else raw.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


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


def _meta() -> dict[str, object]:
    return {
        "is_shadow": True,
        "is_advisory": True,
        "is_executable": False,
        "is_truth": False,
        "xrpl_warning": XRPL_ORDER_INTENT_WARNING,
    }
