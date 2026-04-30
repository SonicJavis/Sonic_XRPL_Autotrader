from __future__ import annotations

from typing import Any

from app.config import Settings
from app.execution.execution_guard import ExecutionGuard


def build_trustset_tx(account: str, issuer: str, currency: str, limit: str) -> dict[str, Any]:
    return {
        "TransactionType": "TrustSet",
        "Account": account,
        "LimitAmount": {"currency": currency, "issuer": issuer, "value": limit},
    }


def build_offer_create_tx(account: str, taker_gets: Any, taker_pays: Any) -> dict[str, Any]:
    return {
        "TransactionType": "OfferCreate",
        "Account": account,
        "TakerGets": taker_gets,
        "TakerPays": taker_pays,
    }


def build_self_swap_payment_placeholder(account: str, destination: str) -> dict[str, Any]:
    return {
        "TransactionType": "Payment",
        "Account": account,
        "Destination": destination,
        "Note": "Placeholder only - self swap logic not implemented.",
    }


def submit_transaction(settings: Settings, tx_blob: dict[str, Any]) -> None:
    ExecutionGuard(settings).enforce(operation="submit_transaction", payload=tx_blob)
