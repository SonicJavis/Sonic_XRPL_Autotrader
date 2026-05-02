"""XRPL latency estimation for simulation.

XRPL closes a new ledger approximately every 3-5 seconds.
Network roundtrip to public nodes varies by geography.
"""

from __future__ import annotations

from dataclasses import dataclass

# XRPL ledger timing constants
MIN_LEDGER_CLOSE_MS = 3_000
MAX_LEDGER_CLOSE_MS = 5_000
TYPICAL_LEDGER_CLOSE_MS = 4_000


@dataclass
class LatencyEstimate:
    """Estimated end-to-end latency for a ledger operation."""

    ledger_close_ms: int
    network_ms: int
    total_ms: int
    notes: str = ""


def estimate_latency(
    network_ms: int = 150,
    worst_case: bool = False,
) -> LatencyEstimate:
    """Estimate total latency for an XRPL operation.

    Args:
        network_ms: Estimated network roundtrip in milliseconds.
        worst_case: If True, use worst-case ledger close time.

    Returns:
        LatencyEstimate with component breakdown.
    """
    ledger_close = MAX_LEDGER_CLOSE_MS if worst_case else TYPICAL_LEDGER_CLOSE_MS
    total = ledger_close + network_ms

    return LatencyEstimate(
        ledger_close_ms=ledger_close,
        network_ms=network_ms,
        total_ms=total,
        notes=(
            f"XRPL ledger close ~{ledger_close}ms + "
            f"network ~{network_ms}ms = {total}ms total"
        ),
    )
