from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from hashlib import sha256
from math import isfinite
from typing import Iterable, Mapping


PAPER_EXECUTION_SCHEMA_VERSION = "1.0"
XRPL_PAPER_EXECUTION_WARNING = (
    "Paper execution simulations are deterministic, advisory, shadow-only, and non-executing"
)


@dataclass(frozen=True, slots=True)
class XRPLQualityLevel:
    quality: float
    price: float
    available_size: float
    funded: bool = True

    @staticmethod
    def from_mapping(row: Mapping[str, object]) -> "XRPLQualityLevel":
        price = _non_negative(row.get("price", row.get("price_xrp_per_token", row.get("quality", 0.0))))
        return XRPLQualityLevel(
            quality=_non_negative(row.get("quality", price)),
            price=price,
            available_size=_non_negative(row.get("available_size", row.get("xrp_value", row.get("size", row.get("token_amount", 0.0))))),
            funded=bool(row.get("funded", True)),
        )


@dataclass(frozen=True, slots=True)
class XRPLPaperExecutionResult:
    simulation_id: str
    intent_id: str
    schema_version: str
    executed_action: str
    requested_size: float
    filled_size: float
    fill_ratio: float
    avg_execution_price: float
    slippage_realized: float
    execution_status: str
    failure_reason: str
    xrpl_execution_context: dict[str, object]
    pathfinding: dict[str, object]
    issuer_friction: dict[str, object]
    execution_feasibility: dict[str, object]
    is_shadow: bool = True
    is_advisory: bool = True
    is_executable: bool = False
    is_truth: bool = False

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["schema_version"] = PAPER_EXECUTION_SCHEMA_VERSION
        data["simulation_id"] = compute_simulation_id(data)
        data["requested_size"] = round(_non_negative(data["requested_size"]), 6)
        data["filled_size"] = round(_non_negative(data["filled_size"]), 6)
        data["fill_ratio"] = round(_unit(data["fill_ratio"]), 6)
        data["avg_execution_price"] = round(_non_negative(data["avg_execution_price"]), 6)
        data["slippage_realized"] = round(_non_negative(data["slippage_realized"]), 6)
        data["xrpl_execution_context"] = _sanitize_mapping(data["xrpl_execution_context"])
        data["pathfinding"] = _sanitize_mapping(data["pathfinding"])
        data["issuer_friction"] = _sanitize_mapping(data["issuer_friction"])
        data["execution_feasibility"] = _sanitize_mapping(data["execution_feasibility"])
        data["is_shadow"] = True
        data["is_advisory"] = True
        data["is_executable"] = False
        data["is_truth"] = False
        return {key: data[key] for key in sorted(data)}


class XRPLPaperExecutionEngine:
    def simulate(
        self,
        *,
        intent: Mapping[str, object],
        quality_levels: Iterable[XRPLQualityLevel | Mapping[str, object]],
        transfer_fee_bps: int = 0,
        trustline_available: bool = True,
        snapshot_complete: bool = True,
    ) -> XRPLPaperExecutionResult:
        intent_id = str(intent.get("intent_id", ""))
        action = str(intent.get("action", "avoid")).lower()
        requested_size = _non_negative(intent.get("proposed_size", intent.get("requested_size", 0.0)))
        original_requested_size = requested_size
        context = dict(intent.get("xrpl_context") or {}) if isinstance(intent.get("xrpl_context"), Mapping) else {}
        estimates = dict(intent.get("execution_estimates") or {}) if isinstance(intent.get("execution_estimates"), Mapping) else {}
        path = dict(intent.get("pathfinding") or {}) if isinstance(intent.get("pathfinding"), Mapping) else {}
        feasibility = dict(intent.get("execution_feasibility") or {}) if isinstance(intent.get("execution_feasibility"), Mapping) else {}
        expected_price = _non_negative(estimates.get("reference_price", estimates.get("expected_price", 0.0)))
        path_required = bool(path.get("path_required", False))
        path_viability = _unit(path.get("path_viability_score", 1.0), default=1.0)
        ledger_index = max(0, int(_finite(context.get("ledger_index", 0))))
        validated = bool(context.get("validated", False))
        fee_bps = max(0, int(_finite(transfer_fee_bps)))

        levels = sorted(
            [_level(row) for row in quality_levels],
            key=lambda row: (row.quality, row.price, row.available_size),
        )
        funded_levels = [row for row in levels if row.funded and row.available_size > 0.0 and row.price > 0.0]

        failure_reason = ""
        path_used = "direct"
        if action == "avoid":
            failure_reason = "constraint"
        elif feasibility.get("decision") == "avoid":
            failure_reason = "constraint"
        elif not validated or not snapshot_complete:
            failure_reason = "incomplete_snapshot"
        elif not trustline_available or fee_bps >= 5000:
            failure_reason = "constraint"
        elif path_required and path_viability < 0.35:
            failure_reason = "path"
            path_used = "none"
        elif path_required:
            path_used = "multi-hop" if path_viability < 0.75 else "direct"
        if not failure_reason and (requested_size <= 0.0 or not funded_levels):
            failure_reason = "liquidity"

        filled_size = 0.0
        gross_size = 0.0
        weighted_price = 0.0
        levels_consumed = 0
        offers_consumed = 0
        if not failure_reason:
            feasibility_cap = _non_negative(feasibility.get("weakest_hop_capacity", requested_size), default=requested_size)
            expected_fill_ratio = _unit(feasibility.get("expected_fill_ratio", 1.0), default=1.0)
            max_fill_size = min(requested_size, feasibility_cap, requested_size * expected_fill_ratio)
            path_multiplier = 1.0 if not path_required else max(0.0, min(0.85, path_viability))
            fee_multiplier = max(0.0, 1.0 - (fee_bps / 10_000.0))
            target_gross = max_fill_size / max(fee_multiplier, 1e-9)
            remaining_gross = target_gross
            for level in funded_levels:
                if remaining_gross <= 0.0:
                    break
                available = level.available_size * path_multiplier
                consumed = min(available, remaining_gross)
                if consumed <= 0.0:
                    continue
                gross_size += consumed
                filled_size += consumed * fee_multiplier
                weighted_price += consumed * level.price
                remaining_gross -= consumed
                levels_consumed += 1
                offers_consumed += 1

        avg_price = 0.0 if gross_size <= 0.0 else weighted_price / gross_size
        if expected_price <= 0.0 and funded_levels:
            expected_price = funded_levels[0].price
        transfer_fee_slippage = fee_bps / 10_000.0
        slippage = 0.0 if expected_price <= 0.0 or avg_price <= 0.0 else max(0.0, (avg_price - expected_price) / expected_price)
        slippage += transfer_fee_slippage
        fill_ratio = _unit(filled_size / max(original_requested_size, 1e-9))
        if fill_ratio <= 0.0 and not failure_reason:
            failure_reason = "liquidity"
        status = "failed"
        if fill_ratio >= 0.999:
            status = "full"
            failure_reason = ""
        elif fill_ratio > 0.0:
            status = "partial"
            failure_reason = ""

        result = XRPLPaperExecutionResult(
            simulation_id="",
            intent_id=intent_id,
            schema_version=PAPER_EXECUTION_SCHEMA_VERSION,
            executed_action=action if action in {"buy", "sell", "avoid"} else "avoid",
            requested_size=original_requested_size,
            filled_size=min(filled_size, original_requested_size),
            fill_ratio=fill_ratio,
            avg_execution_price=avg_price,
            slippage_realized=slippage,
            execution_status=status,
            failure_reason=failure_reason,
            xrpl_execution_context={
                "ledger_index": ledger_index,
                "quality_levels_consumed": levels_consumed,
                "offers_consumed": offers_consumed,
                "funded_liquidity_only": True,
            },
            pathfinding={
                "path_required": path_required,
                "path_viability_score": round(path_viability, 6),
                "path_used": path_used,
            },
            issuer_friction={
                "transfer_fee_bps": fee_bps,
                "trustline_available": bool(trustline_available),
            },
            execution_feasibility=_simulation_feasibility_context(feasibility),
        )
        return result


def compute_simulation_id(data: Mapping[str, object]) -> str:
    context = dict(data.get("xrpl_execution_context") or {}) if isinstance(data.get("xrpl_execution_context"), Mapping) else {}
    issuer_friction = dict(data.get("issuer_friction") or {}) if isinstance(data.get("issuer_friction"), Mapping) else {}
    pattern = {
        "schema_version": str(data.get("schema_version", PAPER_EXECUTION_SCHEMA_VERSION)),
        "intent_id": str(data.get("intent_id", "")),
        "executed_action": str(data.get("executed_action", "")),
        "requested_size": round(_non_negative(data.get("requested_size", 0.0)), 6),
        "filled_size": round(_non_negative(data.get("filled_size", 0.0)), 6),
        "fill_ratio": round(_unit(data.get("fill_ratio", 0.0)), 6),
        "avg_execution_price": round(_non_negative(data.get("avg_execution_price", 0.0)), 6),
        "ledger_index": int(_finite(context.get("ledger_index", 0))),
        "quality_levels_consumed": int(_finite(context.get("quality_levels_consumed", 0))),
        "transfer_fee_bps": int(_finite(issuer_friction.get("transfer_fee_bps", 0))),
    }
    encoded = json.dumps(pattern, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sim_{sha256(encoded).hexdigest()[:24]}"


def summarize_simulations(results: Iterable[XRPLPaperExecutionResult | Mapping[str, object]]) -> dict[str, object]:
    rows = [row.to_dict() if isinstance(row, XRPLPaperExecutionResult) else dict(row) for row in results]
    count = len(rows)
    failed = sum(1 for row in rows if row.get("execution_status") == "failed")
    return {
        "schema_version": PAPER_EXECUTION_SCHEMA_VERSION,
        "count": count,
        "avg_fill_ratio": round(_avg(row.get("fill_ratio", 0.0) for row in rows), 6),
        "avg_slippage": round(_avg(row.get("slippage_realized", 0.0) for row in rows), 6),
        "failure_rate": 0.0 if count == 0 else round(failed / count, 6),
        "success_rate": 0.0 if count == 0 else round((count - failed) / count, 6),
        **_meta(),
    }


def _level(row: XRPLQualityLevel | Mapping[str, object]) -> XRPLQualityLevel:
    if isinstance(row, XRPLQualityLevel):
        return row
    return XRPLQualityLevel.from_mapping(row)


def _sanitize_mapping(data: Mapping[str, object]) -> dict[str, object]:
    clean: dict[str, object] = {}
    for key, value in sorted(data.items()):
        if isinstance(value, bool):
            clean[str(key)] = value
        elif isinstance(value, int):
            clean[str(key)] = int(value)
        elif isinstance(value, float):
            clean[str(key)] = round(_finite(value), 6)
        elif isinstance(value, Mapping):
            clean[str(key)] = _sanitize_mapping(value)
        elif isinstance(value, list):
            clean[str(key)] = [
                _sanitize_mapping(item) if isinstance(item, Mapping) else item
                for item in value
            ]
        else:
            clean[str(key)] = value
    return clean


def _simulation_feasibility_context(feasibility: Mapping[str, object]) -> dict[str, object]:
    if not feasibility:
        return {
            "schema_version": "1.0",
            "execution_feasibility_score": 0.0,
            "decision": "avoid",
            "route_type": "none",
            "expected_fill_ratio": 0.0,
            "expected_slippage": 0.0,
            "weakest_hop_capacity": 0.0,
            "avoid_reason": "missing_feasibility_context",
            "is_shadow": True,
            "is_advisory": True,
            "is_executable": False,
            "is_truth": False,
        }
    return {
        "schema_version": str(feasibility.get("schema_version", "1.0")),
        "execution_feasibility_score": _unit(feasibility.get("execution_feasibility_score", 0.0)),
        "decision": str(feasibility.get("decision", "avoid")),
        "route_type": str(feasibility.get("route_type", "none")),
        "expected_fill_ratio": _unit(feasibility.get("expected_fill_ratio", 0.0)),
        "expected_slippage": _unit(feasibility.get("expected_slippage", 0.0)),
        "weakest_hop_capacity": _non_negative(feasibility.get("weakest_hop_capacity", 0.0)),
        "avoid_reason": feasibility.get("avoid_reason"),
        "is_shadow": True,
        "is_advisory": True,
        "is_executable": False,
        "is_truth": False,
    }


def _avg(values: Iterable[object]) -> float:
    rows = [_finite(value) for value in values]
    return 0.0 if not rows else sum(rows) / len(rows)


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
        "xrpl_warning": XRPL_PAPER_EXECUTION_WARNING,
    }
