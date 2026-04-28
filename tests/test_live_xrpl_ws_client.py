from app.live.xrpl_ws_client import XRPLWebSocketClient


def test_xrpl_ws_client_tracks_ledger_sequence_and_gaps() -> None:
    client = XRPLWebSocketClient("wss://xrpl.example")

    subscribe = client.connect()
    assert subscribe["command"] == "subscribe"
    assert subscribe["streams"] == ["ledger", "validations"]

    first = client.handle_message({"type": "ledgerClosed", "ledger_index": 500})
    second = client.handle_message({"type": "ledgerClosed", "ledger_index": 503})

    assert first is not None
    assert second is not None
    assert first.ledger_closed is True
    assert second.ledger_closed is True

    health = client.health()
    assert health.last_ledger_index == 503
    assert health.missed_ledger_gaps == 2


def test_xrpl_ws_client_reconnects_and_stops_after_limit() -> None:
    client = XRPLWebSocketClient("wss://xrpl.example", include_transactions=True, max_reconnect_attempts=2)

    client.connect()
    resubscribe = client.handle_disconnect("socket_lost")
    assert resubscribe is not None
    assert resubscribe["streams"] == ["ledger", "validations", "transactions"]
    assert client.health().reconnect_count == 1

    resubscribe = client.handle_disconnect("socket_lost_again")
    assert resubscribe is not None
    assert client.health().reconnect_count == 2

    resubscribe = client.handle_disconnect("permanent_failure")
    assert resubscribe is None
    assert client.connected is False


def test_xrpl_ws_client_handles_validation_messages_as_ledger_events() -> None:
    client = XRPLWebSocketClient("wss://xrpl.example")
    client.connect()

    event = client.handle_message({"type": "validationReceived", "ledger_index": 900})

    assert event is not None
    assert event.ledger_closed is True
    assert client.health().last_ledger_index == 900