"""XRPL fee estimation for simulation.

XRPL fees are in XRP drops (1 XRP = 1,000,000 drops).
Base fee is 12 drops. Escalation depends on ledger load.
"""

from __future__ import annotations

from dataclasses import dataclass

# XRPL constants
BASE_FEE_DROPS = 12
XRP_PER_DROP = 1 / 1_000_000


@dataclass
class FeeEstimate:
    """Estimated transaction fee for an XRPL transaction."""

    base_fee_drops: int
    escalated_fee_drops: int
    notes: str = ""

    @property
    def base_fee_xrp(self) -> float:
        return self.base_fee_drops * XRP_PER_DROP

    @property
    def escalated_fee_xrp(self) -> float:
        return self.escalated_fee_drops * XRP_PER_DROP


def estimate_fee(
    tx_type: str = "Payment",
    load_factor: float = 1.0,
) -> FeeEstimate:
    """Estimate the fee for an XRPL transaction.

    Args:
        tx_type: XRPL transaction type (e.g. 'Payment', 'OfferCreate').
        load_factor: Current network load factor (1.0 = normal).
                     Escalates fees under high load.

    Returns:
        FeeEstimate with base and escalated fee in drops.
    """
    # Standard fees per transaction type
    type_multipliers = {
        "Payment": 1,
        "OfferCreate": 1,
        "OfferCancel": 1,
        "AMMDeposit": 1,
        "AMMWithdraw": 1,
        "AMMSwap": 1,
        "EscrowCreate": 1,
        "TrustSet": 1,
    }
    multiplier = type_multipliers.get(tx_type, 1)

    base = BASE_FEE_DROPS * multiplier
    escalated = int(base * max(1.0, load_factor))

    return FeeEstimate(
        base_fee_drops=base,
        escalated_fee_drops=escalated,
        notes=f"tx_type={tx_type!r}, load_factor={load_factor}",
    )
