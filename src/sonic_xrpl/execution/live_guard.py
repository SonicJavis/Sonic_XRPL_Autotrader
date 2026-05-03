"""Execution Live Guard — blocks all live trading in Phase 45.

This is the primary safety gate for the V2 execution domain.

Functions exposed:
- assert_live_disabled()        — always raises, unconditionally
- assert_can_create_intent(mode) — raises for read-only modes
- assert_can_simulate(mode)      — raises for non-simulation modes
- assert_can_paper_trade(mode)   — raises for non-paper modes
- assert_can_submit(mode)        — ALWAYS raises (Phase 45)
- block_signing()                — always raises
- block_autofill()               — always raises
- block_wallet_construction()    — always raises

Do NOT modify this file to enable live trading without:
1. Explicit user permission
2. Security review (Phase 57)
3. Full audit validator pass
"""

from __future__ import annotations

from sonic_xrpl.core.errors import LiveTradingDisabledError, ModeViolationError
from sonic_xrpl.core.modes import RuntimeMode


def assert_live_disabled() -> None:
    """Unconditionally raise LiveTradingDisabledError.

    Called at module init of any live-trading path to ensure
    live trading cannot accidentally be enabled.
    """
    raise LiveTradingDisabledError(
        "Live trading is disabled in Phase 45. "
        "No signing, submission, or wallet construction is permitted."
    )


def assert_can_create_intent(mode: RuntimeMode) -> None:
    """Raise ModeViolationError if intent creation is not allowed in this mode."""
    allowed = (RuntimeMode.SIMULATION, RuntimeMode.PAPER)
    if mode not in allowed:
        raise ModeViolationError(
            f"Cannot create execution intent in mode {mode.value!r}. "
            f"Allowed modes: {[m.value for m in allowed]}"
        )


def assert_can_simulate(mode: RuntimeMode) -> None:
    """Raise ModeViolationError if simulation is not allowed in this mode."""
    if mode != RuntimeMode.SIMULATION:
        raise ModeViolationError(
            f"Cannot run simulation in mode {mode.value!r}. "
            f"Simulation requires mode: {RuntimeMode.SIMULATION.value!r}"
        )


def assert_can_paper_trade(mode: RuntimeMode) -> None:
    """Raise ModeViolationError if paper trading is not allowed in this mode."""
    if mode != RuntimeMode.PAPER:
        raise ModeViolationError(
            f"Cannot paper trade in mode {mode.value!r}. "
            f"Paper trading requires mode: {RuntimeMode.PAPER.value!r}"
        )


def assert_can_submit(mode: RuntimeMode) -> None:
    """ALWAYS raise LiveTradingDisabledError.

    Transaction submission is unconditionally blocked in Phase 45.
    This guard MUST remain in place until Phase 57 security review is complete
    and explicit user permission is granted.
    """
    raise LiveTradingDisabledError(
        f"assert_can_submit() called with mode={mode.value!r} — "
        "transaction submission is unconditionally blocked in Phase 45. "
        "See docs/SAFETY_MODEL.md for the live trading enablement path."
    )


def block_signing() -> None:
    """Block any attempt to sign a transaction."""
    raise LiveTradingDisabledError(
        "Transaction signing is blocked in Phase 45."
    )


def block_autofill() -> None:
    """Block any attempt to autofill transaction fields."""
    raise LiveTradingDisabledError(
        "Transaction autofill is blocked in Phase 45."
    )


def block_wallet_construction() -> None:
    """Block any attempt to construct a wallet from seed/private key."""
    raise LiveTradingDisabledError(
        "Wallet construction from seed or private key is blocked in Phase 45."
    )
