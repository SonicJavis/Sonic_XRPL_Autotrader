from datetime import datetime, timezone

from app.live.xrpl_book_offers_adapter import XRPLBookOffersAdapter, XRPLWatchedTokenRef
from app.live.xrpl_ingestion_models import XRPLLedgerEvent


class FakeBookClient:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def book_offers(self, *, token, ledger_index):
        self.calls.append((token, ledger_index))
        return self.payload


def _token() -> XRPLWatchedTokenRef:
    return XRPLWatchedTokenRef(token_id=1, issuer="rIssuer", currency="USD", is_xrp=False)


def _ledger(index=100) -> XRPLLedgerEvent:
    return XRPLLedgerEvent(index, "hash", datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc), True, {})


def test_empty_book_returns_none() -> None:
    adapter = XRPLBookOffersAdapter(FakeBookClient({"ledger_index": 100, "bids": [], "asks": []}))

    assert adapter.fetch_book_snapshot(_token(), _ledger()) is None
    assert adapter.reason == "EMPTY_BOOK"


def test_malformed_offers_return_none() -> None:
    adapter = XRPLBookOffersAdapter(FakeBookClient({"ledger_index": 100, "bids": ["bad"], "asks": ["bad"]}))

    assert adapter.fetch_book_snapshot(_token(), _ledger()) is None


def test_valid_mock_response_creates_conservative_snapshot() -> None:
    adapter = XRPLBookOffersAdapter(
        FakeBookClient(
            {
                "ledger_index": 100,
                "bids": [{"price": 0.99, "xrp_value": 50.0}],
                "asks": [{"price": 1.01, "xrp_value": 40.0}],
            }
        )
    )

    snap = adapter.fetch_book_snapshot(_token(), _ledger())

    assert snap is not None
    assert snap.best_bid == 0.99
    assert snap.best_ask == 1.01
    assert snap.bid_depth_xrp == 50.0
    assert snap.ask_depth_xrp == 40.0
    assert snap.spread_pct > 0.0


def test_stale_ledger_rejected() -> None:
    adapter = XRPLBookOffersAdapter(
        FakeBookClient(
            {
                "ledger_index": 90,
                "bids": [{"price": 0.99, "xrp_value": 50.0}],
                "asks": [{"price": 1.01, "xrp_value": 40.0}],
            }
        )
    )

    assert adapter.fetch_book_snapshot(_token(), _ledger(100)) is None
    assert adapter.stale_snapshot_count == 1
