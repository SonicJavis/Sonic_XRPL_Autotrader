from datetime import datetime, timezone
from math import isfinite

from app.live.xrpl_book_offers_adapter import XRPLBookOffersAdapter, XRPLWatchedTokenRef
from app.live.xrpl_readonly_ws_adapter import XRPLReadOnlyWebSocketAdapter
from app.live.xrpl_ws_snapshot_source import XRPLWebSocketSnapshotSource


class FakeWs:
    def __init__(self, messages):
        self.messages = list(messages)

    def connect(self):
        return True

    def receive(self):
        return self.messages.pop(0) if self.messages else None


class FakeBooks:
    def __init__(self, payload):
        self.payload = payload

    def book_offers(self, *, token, ledger_index):
        return self.payload


def _source(messages, payload, tokens=None):
    ws = XRPLReadOnlyWebSocketAdapter(FakeWs(messages))
    ws.connect()
    return XRPLWebSocketSnapshotSource(
        ws_adapter=ws,
        book_adapter=XRPLBookOffersAdapter(FakeBooks(payload)),
        watched_tokens_provider=lambda: tokens if tokens is not None else [XRPLWatchedTokenRef(1, "rIssuer", "USD")],
        default_requested_size=100.0,
    )


def test_no_ledger_event_returns_none() -> None:
    assert _source([], {}).next_snapshot() is None


def test_no_watched_token_returns_none() -> None:
    source = _source([{"ledger_index": 100, "validated": True}], {}, tokens=[])

    assert source.next_snapshot() is None
    assert source.reason == "NO_WATCHED_TOKEN"


def test_stale_snapshot_returns_none() -> None:
    source = _source(
        [{"ledger_index": 100, "validated": True}],
        {"ledger_index": 90, "bids": [{"price": 0.9, "xrp_value": 10}], "asks": [{"price": 1.1, "xrp_value": 10}]},
    )

    assert source.next_snapshot() is None
    assert source.health().stale_snapshot_count > 0


def test_valid_mock_ledger_and_book_emit_shadow_snapshot() -> None:
    source = _source(
        [{"ledger_index": 100, "validated": True, "close_time_iso": "2026-04-28T12:00:00+00:00"}],
        {"ledger_index": 100, "bids": [{"price": 0.9, "xrp_value": 80}], "asks": [{"price": 1.1, "xrp_value": 40}]},
    )

    snap = source.next_snapshot()

    assert snap is not None
    assert snap.ledger_index == 100
    assert snap.execution_price_proxy == 1.1
    assert snap.snapshot_derived_liquidity == 40.0
    assert snap.observed_possible_fill <= snap.snapshot_derived_liquidity
    assert snap.route_instability == 0.25
    assert snap.competition_penalty == 0.25
    assert snap.slippage_estimate >= 0.0
    assert isfinite(snap.slippage_estimate)


def test_ledger_regression_and_gap_increment_counters() -> None:
    source = _source(
        [{"ledger_index": 100, "validated": True}, {"ledger_index": 90, "validated": True}, {"ledger_index": 300, "validated": True}],
        {"ledger_index": 100, "bids": [{"price": 0.9, "xrp_value": 80}], "asks": [{"price": 1.1, "xrp_value": 40}]},
    )
    assert source.next_snapshot() is not None
    assert source.next_snapshot() is None
    assert source.next_snapshot() is None
    health = source.health()
    assert health.rejected_snapshot_count >= 1
    assert health.stale_snapshot_count >= 1
