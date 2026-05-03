"""Python-side balance change extraction from XRPL transaction metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sonic_xrpl.providers.metadata_parser import extract_affected_nodes


@dataclass
class BalanceChange:
    account: str
    currency: str
    issuer: str | None  # None for XRP
    value: str  # string to preserve precision, can be negative

    @property
    def asset_key(self) -> str:
        if self.issuer:
            return f"{self.currency}:{self.issuer}"
        return "XRP"


def _drops_diff(final: str | None, previous: str | None) -> str | None:
    """Compute XRP drop difference as a string."""
    if final is None or previous is None:
        return None
    try:
        diff = int(final) - int(previous)
        return str(diff)
    except (ValueError, TypeError):
        return None


def _iou_diff(
    final_balance: dict[str, Any] | None,
    previous_balance: dict[str, Any] | None,
) -> tuple[str, str, str] | None:
    """Return (currency, issuer, value_diff) for RippleState balance change."""
    if final_balance is None or previous_balance is None:
        return None
    currency = final_balance.get("currency", "")
    issuer = final_balance.get("issuer", "")
    try:
        diff = float(final_balance.get("value", "0")) - float(previous_balance.get("value", "0"))
        return currency, issuer, str(diff)
    except (ValueError, TypeError):
        return None


def extract_balance_changes(metadata: dict[str, Any]) -> list[BalanceChange]:
    """Extract balance changes from XRPL transaction metadata."""
    if not metadata:
        return []

    nodes = extract_affected_nodes(metadata)
    changes: list[BalanceChange] = []

    for node in nodes:
        if node.ledger_entry_type == "AccountRoot":
            ff = node.final_fields or {}
            pf = node.previous_fields or {}
            account = ff.get("Account", "")
            if not account and node.new_fields:
                account = node.new_fields.get("Account", "")

            final_bal = ff.get("Balance") or (node.new_fields or {}).get("Balance")
            prev_bal = pf.get("Balance")

            if final_bal is not None and prev_bal is not None and account:
                diff = _drops_diff(str(final_bal), str(prev_bal))
                if diff is not None:
                    changes.append(BalanceChange(
                        account=account,
                        currency="XRP",
                        issuer=None,
                        value=diff,
                    ))

        elif node.ledger_entry_type == "RippleState":
            ff = node.final_fields or {}
            pf = node.previous_fields or {}

            final_balance = ff.get("Balance")
            prev_balance = pf.get("Balance")

            if not isinstance(final_balance, dict) or not isinstance(prev_balance, dict):
                continue

            result = _iou_diff(final_balance, prev_balance)
            if result is None:
                continue
            currency, issuer, value = result

            low_limit = ff.get("LowLimit", {})
            account = low_limit.get("issuer", "") if isinstance(low_limit, dict) else ""

            if account and currency and issuer:
                changes.append(BalanceChange(
                    account=account,
                    currency=currency,
                    issuer=issuer,
                    value=value,
                ))

    return changes
