"""Paper trading executor — simulates trades without touching the XRPL."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Session

from app.config import settings
from app.db.models import PaperTrade, Signal
from app.strategies.base import SignalPayload
from app.telemetry import get_logger, new_request_id

logger = get_logger("execution.paper")


class PaperExecutor:
    """Simulate trade entry and exit, tracking P&L in the database."""

    def __init__(self, session: Session) -> None:
        self._session = session

    # ── Entry ────────────────────────────────────────────────────────────────

    def open_trade(
        self,
        signal: SignalPayload,
        signal_id: int | None = None,
        request_id: str | None = None,
    ) -> PaperTrade:
        """Open a simulated paper trade from a signal.

        Args:
            signal: The strategy signal driving this trade.
            signal_id: FK to the persisted Signal row (optional).
            request_id: Trace ID — auto-generated if not provided.

        Returns:
            The newly created PaperTrade (committed to DB).
        """
        request_id = request_id or new_request_id()
        size_xrp = settings.max_trade_xrp  # use max allowed size for paper trades

        trade = PaperTrade(
            request_id=request_id,
            signal_id=signal_id,
            currency=signal.currency,
            issuer=signal.issuer,
            direction=signal.direction,
            entry_price_xrp=signal.price_xrp,
            size_xrp=size_xrp,
            stop_loss_pct=settings.paper_stop_loss_pct,
            take_profit_pct=settings.paper_take_profit_pct,
            status="OPEN",
        )
        self._session.add(trade)
        self._session.commit()
        self._session.refresh(trade)

        logger.info(
            "Paper trade opened",
            request_id=request_id,
            trade_id=trade.id,
            currency=signal.currency,
            direction=signal.direction,
            entry_price_xrp=signal.price_xrp,
            size_xrp=size_xrp,
        )
        return trade

    # ── Exit ─────────────────────────────────────────────────────────────────

    def close_trade(
        self,
        trade: PaperTrade,
        exit_price_xrp: float,
        reason: str = "CLOSED_MANUAL",
    ) -> PaperTrade:
        """Close an open paper trade and calculate P&L.

        This is always allowed — even when the kill switch is active.

        Args:
            trade: The open PaperTrade to close.
            exit_price_xrp: The exit price in XRP.
            reason: Closing reason tag (CLOSED_TP / CLOSED_SL / CLOSED_MANUAL).

        Returns:
            The updated PaperTrade (committed to DB).
        """
        if trade.status != "OPEN":
            logger.warning(
                "Attempted to close a non-open trade",
                trade_id=trade.id,
                current_status=trade.status,
            )
            return trade

        if trade.direction == "BUY":
            pnl = ((exit_price_xrp - trade.entry_price_xrp) / trade.entry_price_xrp) * trade.size_xrp
        else:
            pnl = ((trade.entry_price_xrp - exit_price_xrp) / trade.entry_price_xrp) * trade.size_xrp

        trade.exit_price_xrp = exit_price_xrp
        trade.pnl_xrp = round(pnl, 6)
        trade.status = reason
        trade.closed_at = datetime.now(timezone.utc)

        self._session.add(trade)
        self._session.commit()
        self._session.refresh(trade)

        logger.info(
            "Paper trade closed",
            trade_id=trade.id,
            currency=trade.currency,
            direction=trade.direction,
            entry_price_xrp=trade.entry_price_xrp,
            exit_price_xrp=exit_price_xrp,
            pnl_xrp=trade.pnl_xrp,
            reason=reason,
        )
        return trade

    # ── Tick update ──────────────────────────────────────────────────────────

    def tick(self, trade: PaperTrade, current_price_xrp: float) -> PaperTrade:
        """Check stop-loss / take-profit conditions and close the trade if hit.

        Args:
            trade: An open PaperTrade.
            current_price_xrp: The latest market price.

        Returns:
            The (possibly closed) PaperTrade.
        """
        if trade.status != "OPEN":
            return trade

        entry = trade.entry_price_xrp
        sl_price = entry * (1 - trade.stop_loss_pct)
        tp_price = entry * (1 + trade.take_profit_pct)

        if trade.direction == "BUY":
            if current_price_xrp <= sl_price:
                return self.close_trade(trade, current_price_xrp, reason="CLOSED_SL")
            if current_price_xrp >= tp_price:
                return self.close_trade(trade, current_price_xrp, reason="CLOSED_TP")
        else:
            # SELL — inverse logic
            if current_price_xrp >= sl_price:
                return self.close_trade(trade, current_price_xrp, reason="CLOSED_SL")
            if current_price_xrp <= tp_price:
                return self.close_trade(trade, current_price_xrp, reason="CLOSED_TP")

        return trade
