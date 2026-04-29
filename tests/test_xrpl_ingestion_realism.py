from app.live.xrpl_book_offers_adapter import XRPLBookOffersAdapter, XRPLWatchedTokenRef
from app.live.xrpl_readonly_ws_adapter import XRPLReadOnlyWebSocketAdapter
from app.live.xrpl_ws_snapshot_source import XRPLWebSocketSnapshotSource


class ReplayWs:
    def __init__(self, messages):
        self.messages = list(messages)

    def connect(self):
        return True

    def receive(self):
        return self.messages.pop(0) if self.messages else None


class ReplayBooks:
    def __init__(self, payload):
        self.payload = payload

    def book_offers(self, *, token, ledger_index):
        return self.payload


def _source(messages, payload, **kwargs):
    ws = XRPLReadOnlyWebSocketAdapter(ReplayWs(messages))
    ws.connect()
    return XRPLWebSocketSnapshotSource(
        ws_adapter=ws,
        book_adapter=XRPLBookOffersAdapter(ReplayBooks(payload)),
        watched_tokens_provider=lambda: [XRPLWatchedTokenRef(1, "rIssuer", "USD")],
        default_requested_size=50.0,
        **kwargs,
    )


def test_ingestion_counters_track_gaps_duplicates_and_throttle() -> None:
    payload = {"ledger_index": 100, "bids": [{"price": 0.9, "xrp_value": 120}], "asks": [{"price": 1.1, "xrp_value": 90}]}
    source = _source(
        [
            {"ledger_index": 100, "validated": True},
            {"ledger_index": 100, "validated": True},
            {"ledger_index": 101, "validated": True},
            {"ledger_index": 300, "validated": True},
        ],
        payload,
        snapshot_throttle_ms=5000,
        max_ledger_gap=10,
    )

    assert source.next_snapshot() is not None
    assert source.next_snapshot() is None
    assert source.next_snapshot() is None
    assert source.next_snapshot() is None
    health = source.health()

    assert health.snapshot_count == 1
    assert health.duplicate_ledger_count == 1
    assert health.throttled_snapshot_count == 1
    assert health.ledger_gap_count == 1
    assert 0.0 <= health.snapshot_rejection_rate <= 1.0
    assert health.snapshot_rate_per_sec == 1.0


def test_unfunded_liquidity_estimate_is_non_negative() -> None:
    source = _source(
        [{"ledger_index": 100, "validated": True}],
        {"ledger_index": 100, "bids": [{"price": 0.9, "xrp_value": 200}], "asks": [{"price": 1.1, "xrp_value": 120}]},
    )

    assert source.next_snapshot() is not None
    health = source.health()

    assert health.unfunded_liquidity_estimate == 70.0
    assert health.unfunded_liquidity_estimate >= 0.0
