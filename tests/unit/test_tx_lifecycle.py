from __future__ import annotations

from sonic_xrpl.transaction.lifecycle import LifecycleAction, TransactionLifecycleManager


def test_sequence_collision_maps_to_retry_and_fee_escalation() -> None:
    manager = TransactionLifecycleManager(sequence=10, ledger_index=1000, fee_drops=12)
    decision = manager.evaluate_result("terPRE_SEQ")
    assert decision.action == LifecycleAction.RETRY
    assert decision.reason == "sequence_collision_retry"
    assert decision.next_fee_drops > 12
    assert decision.expected_sequence == 11
    assert decision.last_ledger_sequence == 1004


def test_unfunded_maps_to_retry() -> None:
    manager = TransactionLifecycleManager(sequence=4, ledger_index=900, fee_drops=15)
    decision = manager.evaluate_result("tecUNFUNDED_PAYMENT")
    assert decision.action == LifecycleAction.RETRY
    assert decision.reason == "unfunded_retry_after_balance_refresh"
    assert decision.next_fee_drops >= 15


def test_queued_maps_to_monitor() -> None:
    manager = TransactionLifecycleManager(sequence=33, ledger_index=5000, fee_drops=10)
    decision = manager.evaluate_result("terQUEUED")
    assert decision.action == LifecycleAction.MONITOR
    assert decision.reason == "queued_wait_for_validation"
