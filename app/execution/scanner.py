"""Token scanner — orchestrates the strategy → risk → execution pipeline."""

from __future__ import annotations

import json

from sqlmodel import Session

from app.config import settings
from app.db.models import Signal
from app.db.session import get_session
from app.execution.paper import PaperExecutor
from app.risk.kill_switch import assert_no_kill_switch
from app.risk.rules import RiskDenied, run_all_checks
from app.strategies.base import SignalPayload
from app.strategies.strategy_registry import get_registry
from app.telemetry import get_logger, new_request_id

logger = get_logger("execution.scanner")


def _persist_signal(session: Session, signal: SignalPayload, request_id: str) -> Signal:
    """Save a strategy signal to the database."""
    row = Signal(
        request_id=request_id,
        strategy_name=signal.strategy_name,
        currency=signal.currency,
        issuer=signal.issuer,
        direction=signal.direction,
        price_xrp=signal.price_xrp,
        confidence=signal.confidence,
        metadata_json=json.dumps(signal.metadata),
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def run_scan_cycle() -> list[dict]:
    """Run one scan cycle across all registered strategies.

    Flow per strategy:
        1. generate_signal()
        2. Persist signal to DB
        3. Kill-switch check (blocks new entries only)
        4. Risk checks (position size, open-position count)
        5. PaperExecutor.open_trade()

    Returns:
        List of outcome dicts (one per strategy tick).
    """
    outcomes: list[dict] = []
    registry = get_registry()

    # Resolve the DB session for this cycle.
    session: Session = next(get_session())

    try:
        for strategy_name, strategy in registry.items():
            request_id = new_request_id()
            signal = strategy.generate_signal()

            if signal is None:
                outcomes.append(
                    {"request_id": request_id, "strategy": strategy_name, "result": "no_signal"}
                )
                continue

            # Persist the signal first — always.
            sig_row = _persist_signal(session, signal, request_id)

            # Kill-switch check.
            try:
                assert_no_kill_switch(request_id=request_id)
            except RuntimeError as exc:
                logger.warning(
                    "Trade blocked by kill switch",
                    request_id=request_id,
                    strategy=strategy_name,
                )
                outcomes.append(
                    {
                        "request_id": request_id,
                        "strategy": strategy_name,
                        "result": "kill_switch",
                        "signal_id": sig_row.id,
                        "reason": str(exc),
                    }
                )
                continue

            # Risk checks.
            try:
                run_all_checks(
                    size_xrp=settings.max_trade_xrp,
                    session=session,
                    request_id=request_id,
                )
            except RiskDenied as exc:
                logger.warning(
                    "Trade denied by risk engine",
                    request_id=request_id,
                    strategy=strategy_name,
                    reason=str(exc),
                )
                outcomes.append(
                    {
                        "request_id": request_id,
                        "strategy": strategy_name,
                        "result": "risk_denied",
                        "signal_id": sig_row.id,
                        "reason": str(exc),
                    }
                )
                continue

            # Paper execution.
            executor = PaperExecutor(session)
            trade = executor.open_trade(
                signal=signal,
                signal_id=sig_row.id,
                request_id=request_id,
            )
            outcomes.append(
                {
                    "request_id": request_id,
                    "strategy": strategy_name,
                    "result": "trade_opened",
                    "signal_id": sig_row.id,
                    "trade_id": trade.id,
                }
            )
    finally:
        session.close()

    return outcomes
