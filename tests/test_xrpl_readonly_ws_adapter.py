from app.live.xrpl_readonly_ws_adapter import XRPLReadOnlyWebSocketAdapter, _validate_readonly_command


class FakeWsClient:
    def __init__(self, messages=None, connect_result=True):
        self.messages = list(messages or [])
        self.connect_result = connect_result
        self.sent = []
        self.closed = False

    def connect(self):
        return self.connect_result

    def send(self, command):
        self.sent.append(command)

    def receive(self):
        return self.messages.pop(0) if self.messages else None

    def close(self):
        self.closed = True


def test_subscribe_command_is_read_only() -> None:
    client = FakeWsClient()
    adapter = XRPLReadOnlyWebSocketAdapter(client)

    assert adapter.connect() is True
    assert adapter.subscribe_ledgers() is True
    assert client.sent == [{"command": "subscribe", "streams": ["ledger"]}]


def test_forbidden_outbound_commands_blocked() -> None:
    for command in ("submit", "sign", "wallet", "autofill", "OfferCreate", "Payment"):
        try:
            _validate_readonly_command({"command": command})
        except ValueError:
            pass
        else:
            raise AssertionError(command)


def test_malformed_ledger_messages_return_none() -> None:
    adapter = XRPLReadOnlyWebSocketAdapter(FakeWsClient(messages=[{"ledger_index": 0}, "bad"]))
    adapter.connect()

    assert adapter.next_ledger_event() is None
    assert adapter.reason == "MALFORMED_LEDGER_EVENT"


def test_disconnected_client_returns_none() -> None:
    adapter = XRPLReadOnlyWebSocketAdapter(FakeWsClient())

    assert adapter.next_ledger_event() is None
    assert adapter.health().connected is False


def test_reconnect_and_backoff_are_deterministic_and_capped() -> None:
    adapter = XRPLReadOnlyWebSocketAdapter(FakeWsClient(connect_result=False), max_reconnects=3, base_backoff_seconds=2.0)

    assert adapter.connect() is False
    assert adapter.backoff_seconds == 2.0
    assert adapter.connect() is False
    assert adapter.backoff_seconds == 4.0
    assert adapter.connect() is False
    assert adapter.backoff_seconds == 8.0
    assert adapter.connect() is False
    assert adapter.reason == "MAX_RECONNECTS_EXCEEDED"


def test_valid_ledger_event_updates_health() -> None:
    adapter = XRPLReadOnlyWebSocketAdapter(
        FakeWsClient(messages=[{"type": "ledgerClosed", "ledger_index": 50, "ledger_hash": "abc", "validated": True}])
    )
    adapter.connect()
    event = adapter.next_ledger_event()

    assert event.ledger_index == 50
    assert adapter.health().latest_validated_ledger_index == 50


def test_ledger_time_uses_xrpl_epoch_seconds() -> None:
    adapter = XRPLReadOnlyWebSocketAdapter(
        FakeWsClient(messages=[{"type": "ledgerClosed", "ledger_index": 51, "ledger_time": 0, "validated": True}])
    )
    adapter.connect()

    event = adapter.next_ledger_event()

    assert event.close_time.isoformat() == "2000-01-01T00:00:00+00:00"


def test_only_ledgerclosed_messages_are_parsed_as_ledger_events() -> None:
    adapter = XRPLReadOnlyWebSocketAdapter(
        FakeWsClient(
            messages=[
                {"type": "transactions_proposed", "ledger_index": 51, "validated": True},
                {"ledger_index": 52, "validated": True},
                {"type": "ledgerClosed", "ledger_index": 53, "validated": True},
            ]
        )
    )
    adapter.connect()

    assert adapter.next_ledger_event() is None
    assert adapter.next_ledger_event() is None
    event = adapter.next_ledger_event()

    assert event is not None
    assert event.ledger_index == 53
    assert adapter.health().latest_validated_ledger_index == 53
