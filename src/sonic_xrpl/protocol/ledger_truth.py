"""XRPL ledger truth utilities — helpers for understanding validated vs current ledger state."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LedgerTruth:
    """Snapshot of what we know about the ledger state.

    ledger_index: validated ledger index (authoritative)
    ledger_hash: validated ledger hash
    close_time_iso: ISO 8601 close time of the validated ledger
    is_validated: True if the ledger is fully validated
    """

    ledger_index: int
    ledger_hash: str
    close_time_iso: str
    is_validated: bool

    def __post_init__(self) -> None:
        if self.ledger_index <= 0:
            raise ValueError("ledger_index must be positive")


def is_validated_ledger(data: dict) -> bool:
    """Return True if a rippled ledger response indicates a validated ledger."""
    return bool(data.get("validated", False))
