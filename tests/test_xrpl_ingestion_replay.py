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
    def __init__(self, payloads):
        self.payloads = list(payloads)

    def book_offers(self, *, token, ledger_index):
        return self.payloads.pop(0) if self.payloads else None


def _run_sequence():
    ws = XRPLReadOnlyWebSocketAdapter(ReplayWs([{"ledger_index": 100, "validated": True}, {"ledger_index": 101, "validated": True}]))
    ws.connect()
    source = XRPLWebSocketSnapshotSource(
        ws_adapter=ws,
        book_adapter=XRPLBookOffersAdapter(
            ReplayBooks(
                [
                    {"ledger_index": 100, "bids": [{"price": 0.9, "xrp_value": 40}], "asks": [{"price": 1.1, "xrp_value": 30}]},
                    {"ledger_index": 101, "bids": [{"price": 0.8, "xrp_value": 50}], "asks": [{"price": 1.2, "xrp_value": 20}]},
                ]
            )
        ),
        watched_tokens_provider=lambda: [XRPLWatchedTokenRef(1, "rIssuer", "USD")],
    )
    return [source.next_snapshot(), source.next_snapshot()]


def test_same_fake_sequence_produces_same_snapshot_sequence() -> None:
    first = _run_sequence()
    second = _run_sequence()

    assert first == second


def test_duplicate_ledger_is_deterministic_and_large_gap_rejected() -> None:
    ws = XRPLReadOnlyWebSocketAdapter(
        ReplayWs([{"ledger_index": 100, "validated": True}, {"ledger_index": 100, "validated": True}, {"ledger_index": 999, "validated": True}])
    )
    ws.connect()
    source = XRPLWebSocketSnapshotSource(
        ws_adapter=ws,
        book_adapter=XRPLBookOffersAdapter(
            ReplayBooks(
                [
                    {"ledger_index": 100, "bids": [{"price": 0.9, "xrp_value": 40}], "asks": [{"price": 1.1, "xrp_value": 30}]},
                    {"ledger_index": 100, "bids": [{"price": 0.9, "xrp_value": 40}], "asks": [{"price": 1.1, "xrp_value": 30}]},
                ]
            )
        ),
        watched_tokens_provider=lambda: [XRPLWatchedTokenRef(1, "rIssuer", "USD")],
    )

    assert source.next_snapshot() is not None
    assert source.next_snapshot() is None
    assert source.reason == "DUPLICATE_LEDGER_IGNORED"
    assert source.next_snapshot() is None
    assert source.health().stale_snapshot_count >= 1
