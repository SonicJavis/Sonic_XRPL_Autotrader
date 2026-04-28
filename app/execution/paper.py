from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Session, select

from app.config import Settings
from app.db.models import CapitalLedger, CapitalReservation, PaperTrade
from app.strategies.base import SignalCandidate


class PaperExecutor:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @staticmethod
    def calculate_pnl(side: str, entry_price_xrp: float, exit_price_xrp: float, size_xrp: float) -> float:
        direction = 1.0 if side.upper() == "BUY" else -1.0
        return round((exit_price_xrp - entry_price_xrp) * size_xrp * direction, 10)

    def _get_or_create_ledger(self, session: Session) -> CapitalLedger:
        ledger = session.exec(select(CapitalLedger).order_by(CapitalLedger.id.asc())).first()
        if ledger is not None:
            return ledger
        starting = float(self.settings.STARTING_PAPER_BALANCE_XRP or self.settings.PAPER_STARTING_BALANCE_XRP)
        ledger = CapitalLedger(
            available_balance_xrp=starting,
            locked_balance_xrp=0.0,
            total_balance_xrp=starting,
        )
        session.add(ledger)
        session.commit()
        session.refresh(ledger)
        return ledger

    @staticmethod
    def _sync_total(ledger: CapitalLedger) -> None:
        ledger.total_balance_xrp = float(ledger.available_balance_xrp) + float(ledger.locked_balance_xrp)
        ledger.updated_at = datetime.now(tz=timezone.utc)

    def reserve_capital(
        self,
        session: Session,
        *,
        signal_id: int | None,
        issuer: str,
        currency: str,
        requested_xrp: float,
    ) -> CapitalReservation:
        requested = max(0.0, float(requested_xrp))
        if requested <= 0:
            raise ValueError("capital reservation requires positive requested_xrp")
        if requested > float(self.settings.MAX_POSITION_XRP):
            raise ValueError("requested size exceeds MAX_POSITION_XRP")

        open_positions = session.exec(select(PaperTrade).where(PaperTrade.status == "OPEN")).all()
        if len(open_positions) >= int(self.settings.MAX_CONCURRENT_POSITIONS):
            raise ValueError("max concurrent positions reached")

        ledger = self._get_or_create_ledger(session)
        if (float(ledger.locked_balance_xrp) + requested) > float(self.settings.MAX_TOTAL_LOCKED_XRP):
            raise ValueError("max total locked capital exceeded")
        if requested > float(ledger.available_balance_xrp):
            raise ValueError("insufficient available capital")

        ledger.available_balance_xrp = float(ledger.available_balance_xrp) - requested
        ledger.locked_balance_xrp = float(ledger.locked_balance_xrp) + requested
        if ledger.available_balance_xrp < -1e-9 or ledger.locked_balance_xrp < -1e-9:
            raise ValueError("capital ledger negative balance invariant violated")
        self._sync_total(ledger)

        reservation = CapitalReservation(
            signal_id=signal_id,
            issuer=issuer,
            currency=currency,
            reserved_xrp=requested,
            deployed_xrp=0.0,
            released_xrp=0.0,
            status="ACTIVE",
        )
        session.add(ledger)
        session.add(reservation)
        session.commit()
        session.refresh(reservation)
        return reservation

    def settle_entry_fill(
        self,
        session: Session,
        *,
        reservation_id: int,
        filled_xrp: float,
        failure_reason: str | None = None,
    ) -> CapitalReservation:
        reservation = session.get(CapitalReservation, reservation_id)
        if reservation is None:
            raise ValueError("reservation not found")

        ledger = self._get_or_create_ledger(session)
        filled = max(0.0, float(filled_xrp))
        reserved = float(reservation.reserved_xrp)
        deployed = min(reserved, filled)
        released = max(0.0, reserved - deployed)

        reservation.deployed_xrp = deployed
        reservation.released_xrp = released
        reservation.failure_reason = failure_reason
        reservation.updated_at = datetime.now(tz=timezone.utc)

        if released > 0:
            ledger.locked_balance_xrp = float(ledger.locked_balance_xrp) - released
            ledger.available_balance_xrp = float(ledger.available_balance_xrp) + released

        if deployed <= 1e-12:
            reservation.status = "RELEASED"
            ledger.locked_balance_xrp = max(0.0, float(ledger.locked_balance_xrp) - deployed)
        else:
            reservation.status = "DEPLOYED"

        if ledger.available_balance_xrp < -1e-9 or ledger.locked_balance_xrp < -1e-9:
            raise ValueError("capital ledger negative balance invariant violated")
        self._sync_total(ledger)
        session.add(ledger)
        session.add(reservation)
        session.commit()
        session.refresh(reservation)
        return reservation

    def release_reservation(
        self,
        session: Session,
        *,
        reservation_id: int,
        reason: str,
    ) -> CapitalReservation:
        reservation = session.get(CapitalReservation, reservation_id)
        if reservation is None:
            raise ValueError("reservation not found")

        ledger = self._get_or_create_ledger(session)
        remaining_locked = max(0.0, float(reservation.reserved_xrp) - float(reservation.released_xrp) - float(reservation.deployed_xrp))
        if remaining_locked > 0:
            ledger.locked_balance_xrp = float(ledger.locked_balance_xrp) - remaining_locked
            ledger.available_balance_xrp = float(ledger.available_balance_xrp) + remaining_locked
        reservation.released_xrp = float(reservation.released_xrp) + remaining_locked
        reservation.status = "RELEASED"
        reservation.failure_reason = reason
        reservation.updated_at = datetime.now(tz=timezone.utc)

        if ledger.available_balance_xrp < -1e-9 or ledger.locked_balance_xrp < -1e-9:
            raise ValueError("capital ledger negative balance invariant violated")
        self._sync_total(ledger)
        session.add(ledger)
        session.add(reservation)
        session.commit()
        session.refresh(reservation)
        return reservation

    def open_trade(
        self,
        session: Session,
        candidate: SignalCandidate,
        entry_price_xrp: float,
        *,
        size_xrp: float,
        reservation_id: int,
    ) -> PaperTrade:
        reservation = session.get(CapitalReservation, reservation_id)
        if reservation is None:
            raise ValueError("reservation not found")
        if reservation.status not in {"DEPLOYED", "ACTIVE"}:
            raise ValueError("cannot open trade without active/deployed reservation")
        if float(size_xrp) <= 0:
            raise ValueError("trade size_xrp must be positive")
        if float(size_xrp) - float(reservation.reserved_xrp) > 1e-9:
            raise ValueError("trade size exceeds reserved capital")

        trade = PaperTrade(
            issuer=candidate.issuer,
            currency=candidate.currency,
            side=candidate.side.upper(),
            entry_price_xrp=entry_price_xrp,
            size_xrp=float(size_xrp),
            capital_reservation_id=reservation_id,
            status="OPEN",
        )
        session.add(trade)
        session.commit()
        session.refresh(trade)

        reservation.trade_id = trade.id
        reservation.status = "DEPLOYED"
        reservation.deployed_xrp = float(size_xrp)
        reservation.updated_at = datetime.now(tz=timezone.utc)
        session.add(reservation)
        session.commit()

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

        if trade.capital_reservation_id is not None:
            reservation = session.get(CapitalReservation, trade.capital_reservation_id)
            if reservation is not None:
                ledger = self._get_or_create_ledger(session)
                deployed = float(reservation.deployed_xrp)
                ledger.locked_balance_xrp = max(0.0, float(ledger.locked_balance_xrp) - deployed)
                ledger.available_balance_xrp = float(ledger.available_balance_xrp) + deployed + float(trade.pnl_xrp)
                if ledger.available_balance_xrp < -1e-9 or ledger.locked_balance_xrp < -1e-9:
                    raise ValueError("capital ledger negative balance invariant violated")
                self._sync_total(ledger)
                reservation.status = "CLOSED"
                reservation.updated_at = datetime.now(tz=timezone.utc)
                session.add(ledger)
                session.add(reservation)

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
