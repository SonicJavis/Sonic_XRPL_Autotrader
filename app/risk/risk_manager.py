from __future__ import annotations

from app.config import Settings
from app.risk.kill_switch import KillSwitch
from app.risk.rules import RiskContext, RiskDecision, RiskEvaluation
from app.strategies.base import SignalCandidate


class RiskManager:
    def __init__(self, settings: Settings, kill_switch: KillSwitch) -> None:
        self.settings = settings
        self.kill_switch = kill_switch

    def evaluate(self, candidate: SignalCandidate, context: RiskContext) -> RiskEvaluation:
        if context.is_exit:
            return RiskEvaluation(RiskDecision.APPROVE, "exit allowed", candidate.suggested_size_xrp)

        if self.kill_switch.is_engaged() and candidate.side.upper() in {"BUY", "SELL"}:
            return RiskEvaluation(RiskDecision.DENY, "kill switch engaged", 0.0)

        if context.live_trading_requested and not self.settings.LIVE_TRADING_ENABLED:
            return RiskEvaluation(RiskDecision.DENY, "live trading disabled", 0.0)

        if candidate.suggested_size_xrp > self.settings.MAX_TRADE_XRP:
            return RiskEvaluation(RiskDecision.DENY, "trade size exceeds MAX_TRADE_XRP", 0.0)

        if context.open_positions >= self.settings.MAX_OPEN_POSITIONS:
            return RiskEvaluation(RiskDecision.DENY, "max open positions reached", 0.0)

        projected_exposure = context.total_exposure_xrp + candidate.suggested_size_xrp
        if projected_exposure > self.settings.MAX_TOTAL_EXPOSURE_XRP:
            return RiskEvaluation(RiskDecision.DENY, "max total exposure exceeded", 0.0)

        if context.daily_loss_xrp >= self.settings.MAX_DAILY_LOSS_XRP:
            return RiskEvaluation(RiskDecision.DENY, "max daily loss exceeded", 0.0)

        if context.market_snapshot is not None:
            if context.market_snapshot.liquidity_xrp < self.settings.MIN_LIQUIDITY_XRP:
                return RiskEvaluation(RiskDecision.DENY, "insufficient liquidity", 0.0)
            if context.market_snapshot.spread_pct > self.settings.MAX_SPREAD_PCT:
                return RiskEvaluation(RiskDecision.DENY, "spread above threshold", 0.0)

        return RiskEvaluation(RiskDecision.APPROVE, "approved", candidate.suggested_size_xrp)
