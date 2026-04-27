from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Session, select

from app.config import Settings
from app.db.models import PaperTrade
from app.strategies.base import SignalCandidate


class PaperExecutor:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @staticmethod
    def calculate_pnl(side: str, entry_price_xrp: float, exit_price_xrp: float, size_xrp: float) -> float:
        direction = 1.0 if side.upper() == "BUY" else -1.0
        return round((exit_price_xrp - entry_price_xrp) * size_xrp * direction, 10)

    def open_trade(self, session: Session, candidate: SignalCandidate, entry_price_xrp: float) -> PaperTrade:
        trade = PaperTrade(
            issuer=candidate.issuer,
            currency=candidate.currency,
            side=candidate.side.upper(),
            entry_price_xrp=entry_price_xrp,
            size_xrp=candidate.suggested_size_xrp,
            status="OPEN",
        )
        session.add(trade)
        session.commit()
        session.refresh(trade)
        return trade

    def close_trade(self, session: Session, trade_id: int, exit_price_xrp: float) -> PaperTrade:
        trade = session.get(PaperTrade, trade_id)
        if trade is None:
            raise ValueError("trade not found")
        if trade.status != "OPEN":
            return trade

        trade.exit_price_xrp = exit_price_xrp
        trade.pnl_xrp = self.calculate_pnl(trade.side, trade.entry_price_xrp, exit_price_xrp, trade.size_xrp)
        trade.status = "CLOSED"
        trade.closed_at = datetime.now(tz=timezone.utc)
        session.add(trade)
        session.commit()
        session.refresh(trade)
        return trade

    def check_exit_conditions(self, session: Session, current_price_xrp: float) -> list[PaperTrade]:
        closed: list[PaperTrade] = []
        open_trades = session.exec(select(PaperTrade).where(PaperTrade.status == "OPEN")).all()

        stoploss_pct = self.settings.DEFAULT_STOPLOSS_PCT / 100.0
        take_profit_pct = self.settings.DEFAULT_TAKE_PROFIT_PCT / 100.0

        for trade in open_trades:
            if trade.side == "BUY":
                stoploss_price = trade.entry_price_xrp * (1 - stoploss_pct)
                take_profit_price = trade.entry_price_xrp * (1 + take_profit_pct)
                if current_price_xrp <= stoploss_price or current_price_xrp >= take_profit_price:
                    closed.append(self.close_trade(session, trade.id, current_price_xrp))

        return closed
