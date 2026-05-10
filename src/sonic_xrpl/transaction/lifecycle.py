"""XRPL transaction lifecycle planning (offline and non-submitting)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class LifecycleAction(str, Enum):
    ACCEPT = "accept"
    RETRY = "retry"
    MONITOR = "monitor"
    FAIL = "fail"


@dataclass(frozen=True)
class LifecycleDecision:
    action: LifecycleAction
    reason: str
    next_fee_drops: int
    expected_sequence: int
    last_ledger_sequence: int


class TransactionLifecycleManager:
    """Tracks sequence and maps XRPL engine results to safe next actions."""

    def __init__(self, *, sequence: int, ledger_index: int, fee_drops: int = 12) -> None:
        self.sequence = sequence
        self.ledger_index = ledger_index
        self.fee_drops = fee_drops

    def build_window(self, *, ledger_buffer: int = 4) -> int:
        return self.ledger_index + max(1, ledger_buffer)

    def evaluate_result(self, result_code: str) -> LifecycleDecision:
        code = (result_code or "").strip()
        action = LifecycleAction.FAIL
        reason = "unhandled_result_code"
        fee = self.fee_drops
        next_sequence = self.sequence

        if code in {"tesSUCCESS"}:
            action = LifecycleAction.ACCEPT
            reason = "validated_success"
            next_sequence = self.sequence + 1
        elif code in {"terPRE_SEQ", "tefPAST_SEQ"}:
            action = LifecycleAction.RETRY
            reason = "sequence_collision_retry"
            fee = int(self.fee_drops * 1.5)
            next_sequence = self.sequence + 1
        elif code in {"terQUEUED"}:
            action = LifecycleAction.MONITOR
            reason = "queued_wait_for_validation"
            fee = self.fee_drops
        elif code in {"tecUNFUNDED_PAYMENT", "tecUNFUNDED_OFFER"}:
            action = LifecycleAction.RETRY
            reason = "unfunded_retry_after_balance_refresh"
            fee = int(self.fee_drops * 1.25)
        elif code.startswith("tec"):
            action = LifecycleAction.FAIL
            reason = "tec_terminal"
        elif code.startswith("ter"):
            action = LifecycleAction.RETRY
            reason = "ter_retry"
            fee = int(self.fee_drops * 1.2)

        return LifecycleDecision(
            action=action,
            reason=reason,
            next_fee_drops=max(10, fee),
            expected_sequence=next_sequence,
            last_ledger_sequence=self.build_window(),
        )
