from app.config import Settings
from app.strategies.base import StrategyContext
from app.strategies.new_token_scanner import NewTokenScannerStrategy


def test_new_token_scanner_generates_buy_for_good_book() -> None:
    strategy = NewTokenScannerStrategy(settings=Settings(MIN_LIQUIDITY_XRP=100, MAX_SPREAD_PCT=8))

    signal = strategy.generate_signal(
        StrategyContext(
            issuer="rIssuer",
            currency="USD",
            current_price_xrp=1.0,
            spread_pct=0.5,
            liquidity_xrp=2500,
            bid_count=6,
            ask_count=6,
        )
    )

    assert signal is not None
    assert signal.side == "BUY"


def test_new_token_scanner_rejects_thin_book() -> None:
    strategy = NewTokenScannerStrategy(settings=Settings(MIN_LIQUIDITY_XRP=100, MAX_SPREAD_PCT=8))

    signal = strategy.generate_signal(
        StrategyContext(
            issuer="rIssuer",
            currency="USD",
            current_price_xrp=1.0,
            spread_pct=0.5,
            liquidity_xrp=2500,
            bid_count=1,
            ask_count=1,
        )
    )

    assert signal is not None
    assert signal.side == "HOLD"
