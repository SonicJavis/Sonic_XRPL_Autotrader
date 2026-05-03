"""Account context builder — Phase 47.

Reads account_info fixture data. No live calls. Read-only.
"""

from __future__ import annotations

from typing import Any

from sonic_xrpl.market.models import AccountContext


def build_account_context(
    raw_account_info: dict[str, Any],
    ledger_index: int,
) -> AccountContext:
    """Build an AccountContext from raw account_info fixture data."""
    limitations: list[str] = []

    acct_data = raw_account_info.get("account_data", raw_account_info)

    account = acct_data.get("Account", "")
    if not account:
        limitations.append("Account field missing from account_info fixture")

    balance_drops = str(acct_data.get("Balance", "0"))
    flags = int(acct_data.get("Flags", 0))
    owner_count = int(acct_data.get("OwnerCount", 0))
    sequence = int(acct_data.get("Sequence", 0))
    previous_txn_id = acct_data.get("PreviousTxnID")

    if not raw_account_info.get("validated", False):
        limitations.append("account_info not from a validated ledger")

    return AccountContext(
        account=account,
        ledger_index=ledger_index,
        flags=flags,
        balance_drops=balance_drops,
        owner_count=owner_count,
        sequence=sequence,
        previous_txn_id=previous_txn_id,
        limitations=limitations,
    )
