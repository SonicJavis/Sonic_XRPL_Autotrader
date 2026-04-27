from datetime import datetime, timedelta, timezone

from app.alpha.engine import AlphaEngine
from app.config import Settings
from app.db.models import MarketSnapshot


def _history(count: int, spread: float = 1.0, liq: float = 5000.0, price: float = 1.0) -> list[MarketSnapshot]:
    now = datetime.now(tz=timezone.utc)
    rows: list[MarketSnapshot] = []
    for idx in range(count):
        rows.append(
            MarketSnapshot(
                token_id=1,
                price_xrp=price,
                liquidity_xrp=liq,
                liquidity_bid_xrp=liq / 2,
                liquidity_ask_xrp=liq / 2,
                spread_pct=spread,
                best_bid=price * 0.999,
                best_ask=price * 1.001,
                tx_count=10,
                bid_count=5,
                ask_count=5,
                created_at=now - timedelta(minutes=count - idx),
            )
        )
    return rows


def _book() -> tuple[list[dict[str, float]], list[dict[str, float]]]:
    bids = [
        {"price": 0.99, "token_amount": 1000.0, "xrp_value": 990.0},
        {"price": 0.98, "token_amount": 1000.0, "xrp_value": 980.0},
        {"price": 0.97, "token_amount": 1000.0, "xrp_value": 970.0},
    ]
    asks = [
        {"price": 1.01, "token_amount": 1000.0, "xrp_value": 1010.0},
        {"price": 1.02, "token_amount": 1000.0, "xrp_value": 1020.0},
        {"price": 1.03, "token_amount": 1000.0, "xrp_value": 1030.0},
    ]
    return bids, asks


def test_alpha_rejects_when_spread_missing() -> None:
    engine = AlphaEngine(Settings())
    bids, asks = _book()

    out = engine.evaluate(
        pair="USD:rIssuer",
        spread_pct=None,
        bids=bids,
        asks=asks,
        history=_history(6),
        target_size_xrp=2.0,
        issuer="rIssuer",
    )

    assert out.decision == "REJECT"
    assert any("spread unavailable" in reason for reason in out.reasons)


def test_alpha_rejects_when_book_concentrated() -> None:
    engine = AlphaEngine(Settings())
    bids = [{"price": 1.0, "token_amount": 10000.0, "xrp_value": 10000.0}] + [
        {"price": 0.99, "token_amount": 1.0, "xrp_value": 0.99},
        {"price": 0.98, "token_amount": 1.0, "xrp_value": 0.98},
    ]
    asks = [{"price": 1.01, "token_amount": 10000.0, "xrp_value": 10100.0}] + [
        {"price": 1.02, "token_amount": 1.0, "xrp_value": 1.02},
        {"price": 1.03, "token_amount": 1.0, "xrp_value": 1.03},
    ]

    out = engine.evaluate(
        pair="USD:rIssuer",
        spread_pct=1.0,
        bids=bids,
        asks=asks,
        history=_history(6),
        target_size_xrp=2.0,
        issuer="rIssuer",
    )

    assert out.decision == "REJECT"
    assert any("manipulation" in reason for reason in out.reasons)


def test_alpha_rejects_when_fill_probability_too_low() -> None:
    settings = Settings(ALPHA_MIN_FILL_PROBABILITY=0.9, MAX_TRADE_XRP=5)
    engine = AlphaEngine(settings)
    bids = [{"price": 0.99, "token_amount": 100.0, "xrp_value": 99.0} for _ in range(3)]
    asks = [{"price": 1.01, "token_amount": 0.5, "xrp_value": 0.505} for _ in range(3)]

    out = engine.evaluate(
        pair="USD:rIssuer",
        spread_pct=1.0,
        bids=bids,
        asks=asks,
        history=_history(6),
        target_size_xrp=5.0,
        issuer="rIssuer",
    )

    assert out.decision == "REJECT"
    assert any("fill probability too low" in reason for reason in out.reasons)


def test_alpha_cooldown_triggers_after_failure_burst() -> None:
    settings = Settings(ALPHA_COOLDOWN_FAILURES=3, ALPHA_COOLDOWN_MINUTES=10)
    engine = AlphaEngine(settings)
    now = datetime.now(tz=timezone.utc)

    failures = [now - timedelta(minutes=1), now - timedelta(minutes=2), now - timedelta(minutes=3)]

    assert engine.in_cooldown(failures) is True
