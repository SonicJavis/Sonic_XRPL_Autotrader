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
            if context.market_snapshot.spread_pct is not None and context.market_snapshot.spread_pct > self.settings.MAX_SPREAD_PCT:
                return RiskEvaluation(RiskDecision.DENY, "spread above threshold", 0.0)

        if context.bid_count < 2 or context.ask_count < 2:
            return RiskEvaluation(RiskDecision.DENY, "orderbook too thin", 0.0)

        if self._has_huge_order_gaps(context):
            return RiskEvaluation(RiskDecision.DENY, "orderbook integrity failed: large gaps", 0.0)

        slippage_pct = self._estimate_slippage_pct(candidate.suggested_size_xrp, context.asks or [])
        if slippage_pct > self.settings.MAX_SLIPPAGE_PCT:
            return RiskEvaluation(RiskDecision.DENY, "estimated slippage above threshold", 0.0)

        return RiskEvaluation(RiskDecision.APPROVE, "approved", candidate.suggested_size_xrp)

    @staticmethod
    def _has_huge_order_gaps(context: RiskContext) -> bool:
        asks = context.asks or []
        if len(asks) < 3:
            return False

        prices = [level["price"] for level in asks if level.get("price", 0) > 0]
        if len(prices) < 3:
            return False

        for idx in range(1, len(prices)):
            prev_price = prices[idx - 1]
            if prev_price <= 0:
                continue
            gap_pct = ((prices[idx] - prev_price) / prev_price) * 100.0
            if gap_pct > 15.0:
                return True
        return False

    @staticmethod
    def _estimate_slippage_pct(target_xrp: float, asks: list[dict[str, float]]) -> float:
        if target_xrp <= 0:
            return 0.0
        if not asks:
            return 100.0

        remaining_xrp = target_xrp
        cost_xrp = 0.0
        tokens_bought = 0.0
        for level in asks:
            price = level.get("price", 0.0)
            xrp_value = level.get("xrp_value", 0.0)
            token_amount = level.get("token_amount", 0.0)
            if price <= 0 or xrp_value <= 0 or token_amount <= 0:
                continue

            take_xrp = min(remaining_xrp, xrp_value)
            token_take = (take_xrp / xrp_value) * token_amount
            cost_xrp += take_xrp
            tokens_bought += token_take
            remaining_xrp -= take_xrp
            if remaining_xrp <= 0:
                break

        if tokens_bought <= 0 or remaining_xrp > 0:
            return 100.0

        vwap_price = cost_xrp / tokens_bought
        best_ask = asks[0]["price"] if asks else 0.0
        if best_ask <= 0:
            return 100.0
        return ((vwap_price - best_ask) / best_ask) * 100.0
