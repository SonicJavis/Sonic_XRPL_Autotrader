from __future__ import annotations

import json
from hashlib import sha256

from execution_prototype.intent_contract import ExecutionIntent, ensure_safety_gates


PLACEHOLDER_ACCOUNT = "rMANUAL_ACCOUNT_PLACEHOLDER"
PLACEHOLDER_DESTINATION = "rMANUAL_SELF_DESTINATION"


def build_unsigned_transaction(intent: ExecutionIntent, *, account: str = PLACEHOLDER_ACCOUNT) -> dict[str, object]:
    ensure_safety_gates(intent)
    source = str(intent.liquidity_source_model.get("preferred_source", intent.liquidity_source_model.get("liquidity_source", "unknown")))
    if source == "orderbook":
        tx = _offer_create(intent, account=account)
    elif source in {"amm", "hybrid"}:
        tx = _payment(intent, account=account)
    else:
        raise ValueError("unsupported liquidity source for transaction prototype")
    return _sorted(tx)


def transaction_fingerprint(tx: dict[str, object]) -> str:
    encoded = json.dumps(tx, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"unsigned_{sha256(encoded).hexdigest()[:24]}"


def _offer_create(intent: ExecutionIntent, *, account: str) -> dict[str, object]:
    token_amount = _issued_amount(intent.token, intent.issuer, intent.size)
    xrp_amount = str(int(round(intent.size * 1_000_000)))
    if intent.action == "buy":
        taker_gets: object = token_amount
        taker_pays: object = xrp_amount
    else:
        taker_gets = xrp_amount
        taker_pays = token_amount
    return {
        "TransactionType": "OfferCreate",
        "Account": account,
        "TakerGets": taker_gets,
        "TakerPays": taker_pays,
        "Flags": 0,
        "Memos": [_memo(intent)],
    }


def _payment(intent: ExecutionIntent, *, account: str) -> dict[str, object]:
    token_amount = _issued_amount(intent.token, intent.issuer, intent.size)
    xrp_amount = str(int(round(intent.size * 1_000_000)))
    if intent.action == "buy":
        amount: object = token_amount
        send_max: object = xrp_amount
    else:
        amount = xrp_amount
        send_max = token_amount
    return {
        "TransactionType": "Payment",
        "Account": account,
        "Destination": PLACEHOLDER_DESTINATION,
        "Amount": amount,
        "SendMax": send_max,
        "Flags": 0,
        "Memos": [_memo(intent)],
    }


def _issued_amount(currency: str, issuer: str, value: float) -> dict[str, str]:
    return {
        "currency": currency,
        "issuer": issuer,
        "value": f"{max(0.0, value):.6f}",
    }


def _memo(intent: ExecutionIntent) -> dict[str, dict[str, str]]:
    return {
        "Memo": {
            "MemoType": "5852504C496E74656E74",
            "MemoData": intent.intent_id.encode("utf-8").hex().upper(),
        }
    }


def _sorted(raw: object) -> object:
    if isinstance(raw, dict):
        return {key: _sorted(raw[key]) for key in sorted(raw)}
    if isinstance(raw, list):
        return [_sorted(item) for item in raw]
    return raw
