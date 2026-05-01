from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping

from execution_prototype.intent_contract import ExecutionIntent, ensure_safety_gates, risk_summary, validate_safety_gates
from execution_prototype.xaman_payload import build_deep_link, build_qr_rendering_payload, build_xaman_payload
from execution_prototype.xrpl_tx_builder import build_unsigned_transaction, transaction_fingerprint


CONFIRMATION_PHRASE = "CONFIRM_EXECUTION"


@dataclass(frozen=True, slots=True)
class RiskAcknowledgement:
    confirmation: str
    trade_type_understood: bool
    partial_fill_accepted: bool
    price_impact_understood: bool


def classify_execution_type(intent: ExecutionIntent) -> dict[str, str]:
    source = _source(intent)
    if source == "orderbook":
        return {
            "tx_type": "OfferCreate",
            "label": "Orderbook trade (limit-style)",
            "liquidity_source": source,
        }
    return {
        "tx_type": "Payment",
        "label": "Path-based trade (AMM / routing)",
        "liquidity_source": source,
    }


def execution_reality_messages(intent: ExecutionIntent) -> list[str]:
    tx_type = classify_execution_type(intent)["tx_type"]
    if tx_type == "OfferCreate":
        return [
            "This is a limit-style order.",
            "May partially fill.",
            "Remaining amount may stay on ledger.",
            "Liquidity may change before execution.",
        ]
    return [
        "This is a path-based trade.",
        "Execution depends on available routes.",
        "Route may fail at submission time.",
        "AMM price may shift per ledger.",
    ]


def partial_fill_range(intent: ExecutionIntent) -> dict[str, float]:
    expected = _unit(intent.execution_feasibility.get("expected_fill_ratio", 0.0))
    confidence = _unit(intent.execution_feasibility.get("fill_confidence_score", expected))
    liquidity_fill = _unit(intent.liquidity_source_model.get("expected_fill_ratio", expected))
    spread = max(0.05, abs(expected - confidence), abs(expected - liquidity_fill))
    minimum = max(0.0, min(expected, confidence, liquidity_fill) - spread)
    maximum = min(1.0, max(expected, confidence, liquidity_fill) + spread)
    return {
        "expected_fill_ratio": round(expected, 6),
        "max_fill_estimate": round(maximum, 6),
        "min_fill_estimate": round(minimum, 6),
    }


def liquidity_explanation(intent: ExecutionIntent) -> dict[str, object]:
    source = _source(intent)
    if source == "amm":
        explanation = "Liquidity always exists but price impact increases with size."
    elif source == "orderbook":
        explanation = "Liquidity depends on funded offers; unfunded offers may be removed during execution."
    elif source == "hybrid":
        explanation = "Liquidity may involve both funded offers and AMM reserves; routing remains ledger-dependent."
    else:
        explanation = "Liquidity source is unclear, so this prototype treats the intent conservatively."
    return {"liquidity_source": source, "explanation": explanation}


def freshness_warning(intent: ExecutionIntent) -> dict[str, object]:
    age = _non_negative_int(intent.liquidity_decay.get("snapshot_age_ledgers", 0))
    decay_factor = _unit(intent.liquidity_decay.get("decay_factor", 0.0))
    decision = str(intent.liquidity_decay.get("decision", "invalid")).lower()
    warnings: list[str] = []
    if decision in {"stale", "invalid"}:
        warnings.append("Liquidity may no longer reflect current ledger state.")
    if age > 1:
        warnings.append("XRPL data freshness is ledger-based; each closed ledger can change liquidity.")
    return {
        "blocked": bool(validate_safety_gates(intent)),
        "decay_factor": decay_factor,
        "decision": decision,
        "snapshot_age_ledgers": age,
        "warnings": warnings,
    }


def build_wizard_package(intent: ExecutionIntent, *, account: str = "rMANUAL_ACCOUNT_PLACEHOLDER") -> dict[str, object]:
    ensure_safety_gates(intent)
    tx = build_unsigned_transaction(intent, account=account)
    payload = build_xaman_payload(tx)
    deep_link = build_deep_link(payload)
    package = {
        "steps": [
            "load_intent",
            "validate_safety_gates",
            "classify_execution_type",
            "show_risk_summary",
            "show_execution_uncertainty",
            "build_unsigned_tx",
            "generate_xaman_payload",
            "await_user_confirmation",
            "record_outcome",
        ],
        "intent_id": intent.intent_id,
        "execution_type": classify_execution_type(intent),
        "risk_summary": risk_summary(intent),
        "execution_reality": execution_reality_messages(intent),
        "partial_fill": partial_fill_range(intent),
        "partial_fill_note": "XRPL offers can be partially filled depending on liquidity.",
        "liquidity": liquidity_explanation(intent),
        "freshness": freshness_warning(intent),
        "unsigned_tx": tx,
        "transaction_fingerprint": transaction_fingerprint(tx),
        "xaman_payload": payload,
        "xaman_deep_link": deep_link,
        "xaman_qr": build_qr_rendering_payload(deep_link),
        "xaman_instructions": [
            "Scan with Xaman to sign.",
            "Review transaction before approving.",
        ],
        "confirmation_required": {
            "phrase": CONFIRMATION_PHRASE,
            "trade_type_understood": True,
            "partial_fill_accepted": True,
            "price_impact_understood": True,
        },
        "post_signing_prompt": "Enter transaction hash after external signing and any manual submission step.",
        "post_signing_warning": "Transaction success is NOT guaranteed; ledger validation determines final outcome.",
        "cancel_message": "No transaction submitted. No funds moved.",
        "failure_causes": [
            "insufficient liquidity",
            "path failure",
            "ledger state changed",
            "slippage exceeded",
        ],
        "is_executable": False,
    }
    return _sorted(package)


def require_risk_acknowledgement(acknowledgement: RiskAcknowledgement) -> None:
    if acknowledgement.confirmation != CONFIRMATION_PHRASE:
        raise ValueError("manual confirmation phrase mismatch")
    if not acknowledgement.trade_type_understood:
        raise ValueError("trade type acknowledgement required")
    if not acknowledgement.partial_fill_accepted:
        raise ValueError("partial fill acknowledgement required")
    if not acknowledgement.price_impact_understood:
        raise ValueError("price impact acknowledgement required")


def audit_context(intent: ExecutionIntent) -> dict[str, object]:
    execution_type = classify_execution_type(intent)["tx_type"]
    return {
        "decay_status": str(intent.liquidity_decay.get("decision", "invalid")),
        "execution_type": execution_type,
        "expected_fill_range": partial_fill_range(intent),
        "liquidity_source": _source(intent),
        "user_acknowledged_risk": True,
    }


def _source(intent: ExecutionIntent) -> str:
    return str(
        intent.liquidity_source_model.get(
            "preferred_source",
            intent.liquidity_source_model.get("liquidity_source", "unknown"),
        )
    ).lower()


def _unit(raw: object) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 0.0
    if not isfinite(value):
        return 0.0
    return max(0.0, min(1.0, value))


def _non_negative_int(raw: object) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return 0
    return max(0, value)


def _sorted(raw: object) -> object:
    if isinstance(raw, Mapping):
        return {str(key): _sorted(value) for key, value in sorted(raw.items())}
    if isinstance(raw, list):
        return [_sorted(item) for item in raw]
    if isinstance(raw, float):
        return round(raw if isfinite(raw) else 0.0, 6)
    return raw
