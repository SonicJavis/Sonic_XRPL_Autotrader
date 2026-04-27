from __future__ import annotations

from dataclasses import asdict
import json
import uuid

from sqlmodel import Session, select

from app.config import BotMode, Settings
from app.db.models import AuditEvent, MarketSnapshot, RiskEvent, Signal, WatchedToken
from app.execution.paper import PaperExecutor
from app.execution.scanner import build_scanner_context
from app.market_data.metrics import MarketMetrics
from app.market_data.snapshot_builder import build_snapshot_from_offers
from app.risk.risk_manager import RiskManager
from app.risk.rules import RiskContext, RiskDecision
from app.strategies.strategy_registry import StrategyRegistry
from app.telemetry.events import TelemetryEvent
from app.telemetry.logging import get_logger, log_event
from app.xrpl_core.client import XRPLReadOnlyClient


class ExecutionPipeline:
    def __init__(
        self,
        settings: Settings,
        xrpl_client: XRPLReadOnlyClient,
        strategy_registry: StrategyRegistry,
        risk_manager: RiskManager,
        paper_executor: PaperExecutor,
    ) -> None:
        self.settings = settings
        self.xrpl_client = xrpl_client
        self.strategy_registry = strategy_registry
        self.risk_manager = risk_manager
        self.paper_executor = paper_executor
        self.logger = get_logger()

    def run_once(self, session: Session, current_price_xrp: float = 1.0) -> dict[str, object]:
        request_id = str(uuid.uuid4())
        watched = session.exec(select(WatchedToken).where(WatchedToken.is_active == True).order_by(WatchedToken.id.asc())).all()
        if not watched:
            return {"request_id": request_id, "signals": 0, "paper_trades_opened": 0, "reason": "no watched tokens"}

        executed: list[int] = []
        signals_count = 0

        for token in watched:
            orderbook = self._fetch_orderbook(token)
            snapshot_payload = build_snapshot_from_offers(orderbook.get("offers", []))
            parsed = snapshot_payload["parsed"]

            snapshot = MarketSnapshot(
                token_id=token.id,
                price_xrp=snapshot_payload["price_xrp"] or 0.0,
                liquidity_xrp=float(snapshot_payload["liquidity_xrp"]),
                spread_pct=float(snapshot_payload["spread_pct"] or 0.0),
                best_bid=float(parsed["best_bid"]["price"] if parsed.get("best_bid") else 0.0),
                best_ask=float(parsed["best_ask"]["price"] if parsed.get("best_ask") else 0.0),
                volume_estimate=0.0,
                tx_count=int(snapshot_payload["order_count"]),
                bid_count=int(snapshot_payload["bid_count"]),
                ask_count=int(snapshot_payload["ask_count"]),
            )
            session.add(snapshot)
            session.commit()
            session.refresh(snapshot)

            context = build_scanner_context(
                issuer=token.issuer,
                currency=token.currency,
                price_xrp=snapshot_payload["price_xrp"],
                spread_pct=snapshot_payload["spread_pct"],
                liquidity_xrp=float(snapshot_payload["liquidity_xrp"]),
                bid_count=int(snapshot_payload["bid_count"]),
                ask_count=int(snapshot_payload["ask_count"]),
            )

            candidates = self.strategy_registry.run_all_strategies(context)

            for candidate in candidates:
                signals_count += 1
                signal = Signal(
                    strategy_name=candidate.strategy_name,
                    issuer=candidate.issuer,
                    currency=candidate.currency,
                    side=candidate.side,
                    confidence=candidate.confidence,
                    risk_score=candidate.risk_score,
                    suggested_size_xrp=candidate.suggested_size_xrp,
                    reason=candidate.reason,
                )
                session.add(signal)
                session.commit()
                session.refresh(signal)

                risk_eval = self.risk_manager.evaluate(
                    candidate,
                    RiskContext(
                        open_positions=0,
                        total_exposure_xrp=0.0,
                        daily_loss_xrp=0.0,
                        market_snapshot=MarketMetrics(
                            price_xrp=snapshot_payload["price_xrp"],
                            liquidity_xrp=float(snapshot_payload["liquidity_xrp"]),
                            spread_pct=snapshot_payload["spread_pct"],
                            volume_estimate=0.0,
                            tx_count=int(snapshot_payload["order_count"]),
                            bid_count=int(snapshot_payload["bid_count"]),
                            ask_count=int(snapshot_payload["ask_count"]),
                        ),
                        bid_count=int(snapshot_payload["bid_count"]),
                        ask_count=int(snapshot_payload["ask_count"]),
                        bids=parsed.get("bids", []),
                        asks=parsed.get("asks", []),
                        is_exit=False,
                        live_trading_requested=False,
                    ),
                )

                if risk_eval.decision != RiskDecision.APPROVE:
                    session.add(
                        RiskEvent(
                            event_type="RISK_DENIAL",
                            severity="WARN",
                            reason=risk_eval.reason,
                        )
                    )
                    session.commit()
                    self._audit(
                        session,
                        request_id,
                        "risk_denied",
                        {
                            "signal_id": signal.id,
                            "reason": risk_eval.reason,
                            "snapshot_id": snapshot.id,
                            "orderbook_stats": {
                                "bid_count": snapshot.bid_count,
                                "ask_count": snapshot.ask_count,
                                "spread_pct": snapshot.spread_pct,
                                "liquidity_xrp": snapshot.liquidity_xrp,
                            },
                        },
                    )
                    continue

                if self.settings.BOT_MODE == BotMode.PAPER_TRADING and candidate.side.upper() == "BUY":
                    entry = snapshot_payload["price_xrp"] or current_price_xrp
                    trade = self.paper_executor.open_trade(session, candidate, entry_price_xrp=entry)
                    executed.append(trade.id)
                    self._audit(
                        session,
                        request_id,
                        "paper_trade_opened",
                        {
                            "trade_id": trade.id,
                            "snapshot_id": snapshot.id,
                            "decision_reason": risk_eval.reason,
                        },
                    )

                telemetry = TelemetryEvent(
                    request_id=request_id,
                    event_type="pipeline_signal_processed",
                    strategy=candidate.strategy_name,
                    token=f"{candidate.currency}:{candidate.issuer}",
                    risk_decision=risk_eval.decision.value,
                    execution_result="executed" if candidate.side.upper() == "BUY" else "skipped",
                )
                log_event(self.logger, asdict(telemetry))

        return {
            "request_id": request_id,
            "signals": signals_count,
            "paper_trades_opened": len(executed),
        }

    def _fetch_orderbook(self, token: WatchedToken) -> dict[str, object]:
        if token.is_xrp:
            return {"offers": []}

        taker_gets = {"currency": token.currency, "issuer": token.issuer}
        taker_pays = "1000000"
        ask_book = self.xrpl_client.get_book_offers(taker_gets=taker_gets, taker_pays=taker_pays)

        bid_book = self.xrpl_client.get_book_offers(
            taker_gets=taker_pays,
            taker_pays=taker_gets,
        )

        asks = [dict(offer, side="ask") for offer in ask_book.get("offers", [])]
        bids = [dict(offer, side="bid") for offer in bid_book.get("offers", [])]
        return {"offers": bids + asks}

    @staticmethod
    def _audit(session: Session, request_id: str, event_type: str, payload: dict[str, object]) -> None:
        session.add(AuditEvent(request_id=request_id, event_type=event_type, payload_json=json.dumps(payload, default=str)))
        session.commit()
