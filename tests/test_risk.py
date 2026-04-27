from app.config import Settings
from app.market_data.metrics import MarketMetrics
from app.risk.kill_switch import KillSwitch
from app.risk.risk_manager import RiskManager
from app.risk.rules import RiskContext, RiskDecision
from app.strategies.base import SignalCandidate


def _candidate(size: float = 1.0) -> SignalCandidate:
    return SignalCandidate(
        strategy_name="test",
        issuer="rIssuer",
        currency="USD",
        side="BUY",
        confidence=0.9,
        risk_score=0.2,
        suggested_size_xrp=size,
        reason="test",
        invalidation_condition="none",
    )


def test_kill_switch_blocks_entries() -> None:
    kill_switch = KillSwitch()
    kill_switch.engage()
    manager = RiskManager(Settings(), kill_switch)

    result = manager.evaluate(_candidate(), RiskContext(open_positions=0, total_exposure_xrp=0.0, daily_loss_xrp=0.0))

    assert result.decision == RiskDecision.DENY


def test_kill_switch_allows_exits() -> None:
    kill_switch = KillSwitch()
    kill_switch.engage()
    manager = RiskManager(Settings(), kill_switch)

    result = manager.evaluate(
        _candidate(),
        RiskContext(open_positions=99, total_exposure_xrp=999.0, daily_loss_xrp=999.0, is_exit=True),
    )

    assert result.decision == RiskDecision.APPROVE


def test_risk_denies_oversized_trade() -> None:
    manager = RiskManager(Settings(MAX_TRADE_XRP=0.5), KillSwitch())

    result = manager.evaluate(_candidate(size=2.0), RiskContext(open_positions=0, total_exposure_xrp=0.0, daily_loss_xrp=0.0))

    assert result.decision == RiskDecision.DENY


def test_risk_denies_too_many_open_positions() -> None:
    manager = RiskManager(Settings(MAX_OPEN_POSITIONS=1), KillSwitch())

    result = manager.evaluate(_candidate(size=0.5), RiskContext(open_positions=1, total_exposure_xrp=0.0, daily_loss_xrp=0.0))

    assert result.decision == RiskDecision.DENY


def test_risk_denies_when_no_bids() -> None:
    manager = RiskManager(Settings(), KillSwitch())
    metrics = MarketMetrics(price_xrp=1.0, liquidity_xrp=2000, spread_pct=1.0, volume_estimate=0, tx_count=3)

    result = manager.evaluate(
        _candidate(size=0.5),
        RiskContext(
            open_positions=0,
            total_exposure_xrp=0.0,
            daily_loss_xrp=0.0,
            market_snapshot=metrics,
            bid_count=0,
            ask_count=4,
            asks=[{"price": 1.0, "xrp_value": 1000.0, "token_amount": 1000.0}],
        ),
    )

    assert result.decision == RiskDecision.DENY


def test_risk_denies_high_spread() -> None:
    manager = RiskManager(Settings(MAX_SPREAD_PCT=2.0), KillSwitch())
    metrics = MarketMetrics(price_xrp=1.0, liquidity_xrp=2000, spread_pct=9.0, volume_estimate=0, tx_count=8)

    result = manager.evaluate(
        _candidate(size=0.5),
        RiskContext(
            open_positions=0,
            total_exposure_xrp=0.0,
            daily_loss_xrp=0.0,
            market_snapshot=metrics,
            bid_count=4,
            ask_count=4,
            asks=[{"price": 1.0, "xrp_value": 1000.0, "token_amount": 1000.0}] * 4,
        ),
    )

    assert result.decision == RiskDecision.DENY


def test_risk_denies_low_liquidity() -> None:
    manager = RiskManager(Settings(MIN_LIQUIDITY_XRP=500), KillSwitch())
    metrics = MarketMetrics(price_xrp=1.0, liquidity_xrp=100, spread_pct=1.0, volume_estimate=0, tx_count=8)

    result = manager.evaluate(
        _candidate(size=0.5),
        RiskContext(
            open_positions=0,
            total_exposure_xrp=0.0,
            daily_loss_xrp=0.0,
            market_snapshot=metrics,
            bid_count=4,
            ask_count=4,
            asks=[{"price": 1.0, "xrp_value": 1000.0, "token_amount": 1000.0}] * 4,
        ),
    )

    assert result.decision == RiskDecision.DENY


def test_risk_denies_thin_book() -> None:
    manager = RiskManager(Settings(), KillSwitch())
    metrics = MarketMetrics(price_xrp=1.0, liquidity_xrp=2000, spread_pct=1.0, volume_estimate=0, tx_count=2)

    result = manager.evaluate(
        _candidate(size=0.5),
        RiskContext(
            open_positions=0,
            total_exposure_xrp=0.0,
            daily_loss_xrp=0.0,
            market_snapshot=metrics,
            bid_count=1,
            ask_count=1,
            asks=[{"price": 1.0, "xrp_value": 1000.0, "token_amount": 1000.0}],
        ),
    )

    assert result.decision == RiskDecision.DENY
