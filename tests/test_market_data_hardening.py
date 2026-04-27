from app.config import Settings
from app.market_data.normalization import normalize_amount
from app.market_data.snapshot_builder import build_snapshot_from_offers
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


def test_drops_to_xrp_conversion() -> None:
    assert normalize_amount("1000000") == 1.0


def test_iou_dict_parsing() -> None:
    assert normalize_amount({"currency": "USD", "value": "12.5", "issuer": "rX"}) == 12.5


def test_snapshot_flags_one_sided_dominance() -> None:
    snapshot = build_snapshot_from_offers(
        [
            {"side": "bid", "taker_gets": 10.0, "taker_pays": 10.0, "quality": 1.0},
            {"side": "ask", "taker_gets": 1000.0, "taker_pays": 1000.0, "quality": 1.0},
            {"side": "ask", "taker_gets": 1000.0, "taker_pays": 1000.0, "quality": 1.0},
        ]
    )
    assert snapshot["one_sided_dominance"] is True


def test_risk_rejects_one_sided_or_missing_quote() -> None:
    manager = RiskManager(Settings(), KillSwitch())
    result = manager.evaluate(
        _candidate(),
        RiskContext(
            open_positions=0,
            total_exposure_xrp=0,
            daily_loss_xrp=0,
            bid_count=0,
            ask_count=3,
            asks=[{"price": 1.0, "xrp_value": 10.0, "token_amount": 10.0}],
        ),
    )
    assert result.decision == RiskDecision.DENY


def test_slippage_partial_fill_detection() -> None:
    manager = RiskManager(Settings(MAX_SLIPPAGE_PCT=5), KillSwitch())
    slippage = manager.estimate_slippage(
        100.0,
        asks=[
            {"price": 1.0, "xrp_value": 10.0, "token_amount": 10.0},
            {"price": 1.1, "xrp_value": 10.0, "token_amount": 9.1},
        ],
    )
    assert slippage["fill_possible"] is False
    assert slippage["slippage_pct"] >= 100.0
