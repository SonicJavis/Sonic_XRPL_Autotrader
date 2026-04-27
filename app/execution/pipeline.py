from __future__ import annotations

from dataclasses import asdict
import json
import uuid

from sqlmodel import Session

from app.config import BotMode, Settings
from app.db.models import AuditEvent, RiskEvent, Signal
from app.execution.paper import PaperExecutor
from app.execution.scanner import build_scanner_context
from app.risk.risk_manager import RiskManager
from app.risk.rules import RiskContext, RiskDecision
from app.strategies.strategy_registry import StrategyRegistry
from app.telemetry.events import TelemetryEvent
from app.telemetry.logging import get_logger, log_event


class ExecutionPipeline:
    def __init__(
        self,
        settings: Settings,
        strategy_registry: StrategyRegistry,
        risk_manager: RiskManager,
        paper_executor: PaperExecutor,
    ) -> None:
        self.settings = settings
        self.strategy_registry = strategy_registry
        self.risk_manager = risk_manager
        self.paper_executor = paper_executor
        self.logger = get_logger()

    def run_once(self, session: Session, current_price_xrp: float = 1.0) -> dict[str, object]:
        request_id = str(uuid.uuid4())
        context = build_scanner_context(price_xrp=current_price_xrp)
        candidates = self.strategy_registry.run_all_strategies(context)
        executed: list[int] = []

        for candidate in candidates:
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
                self._audit(session, request_id, "risk_denied", {"signal_id": signal.id, "reason": risk_eval.reason})
                continue

            if self.settings.BOT_MODE == BotMode.PAPER_TRADING and candidate.side.upper() == "BUY":
                trade = self.paper_executor.open_trade(session, candidate, entry_price_xrp=current_price_xrp)
                executed.append(trade.id)
                self._audit(session, request_id, "paper_trade_opened", {"trade_id": trade.id})

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
            "signals": len(candidates),
            "paper_trades_opened": len(executed),
        }

    @staticmethod
    def _audit(session: Session, request_id: str, event_type: str, payload: dict[str, object]) -> None:
        session.add(AuditEvent(request_id=request_id, event_type=event_type, payload_json=json.dumps(payload, default=str)))
        session.commit()
