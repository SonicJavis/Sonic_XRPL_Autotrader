from app.market_data.orderbook_parser import parse_orderbook
from app.market_data.snapshot_builder import calculate_liquidity, calculate_spread, derive_price_from_orderbook


def test_orderbook_parsing_correctness() -> None:
    offers = [
        {"side": "bid", "quality": 0.95, "taker_gets": 950.0, "taker_pays": 1000.0},
        {"side": "ask", "quality": 1.05, "taker_gets": 1000.0, "taker_pays": 1050.0},
    ]
    parsed = parse_orderbook(offers)

    assert parsed["best_bid"]["price"] == 0.95
    assert parsed["best_ask"]["price"] == 1.05


def test_price_derivation_midpoint() -> None:
    parsed = {
        "best_bid": {"price": 0.98},
        "best_ask": {"price": 1.02},
        "bids": [],
        "asks": [],
    }
    assert derive_price_from_orderbook(parsed) == 1.0


def test_spread_calculation() -> None:
    parsed = {
        "best_bid": {"price": 0.98},
        "best_ask": {"price": 1.00},
        "bids": [],
        "asks": [],
    }
    assert round(calculate_spread(parsed), 4) == 2.0


def test_liquidity_calculation() -> None:
    parsed = {
        "bids": [
            {"price": 0.99, "xrp_value": 100.0, "token_amount": 101.0},
            {"price": 0.98, "xrp_value": 200.0, "token_amount": 204.0},
        ],
        "asks": [
            {"price": 1.01, "xrp_value": 150.0, "token_amount": 148.0},
            {"price": 1.02, "xrp_value": 250.0, "token_amount": 245.0},
        ],
        "best_bid": {"price": 0.99},
        "best_ask": {"price": 1.01},
    }

    assert calculate_liquidity(parsed) == 700.0
