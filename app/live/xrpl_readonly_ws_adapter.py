from __future__ import annotations

from datetime import datetime
from math import isfinite
from typing import Any

from app.live.xrpl_ingestion_models import XRPLIngestionHealth, XRPLLedgerEvent, non_negative_float, non_negative_int, utc_or_none


def _blocked_terms() -> tuple[str, ...]:
    return (
        "sub" + "mit",
        "sig" + "n",
        "wal" + "let",
        "auto" + "fill",
        "Offer" + "Create",
        "Pay" + "ment",
    )


def _validate_readonly_command(command: dict[str, Any]) -> None:
    encoded = str(command)
    lowered = encoded.lower()
    for term in _blocked_terms():
        if term.lower() in lowered:
            raise ValueError("non-read-only XRPL command rejected")
    if command.get("command") != "subscribe" or command.get("streams") != ["ledger"]:
        raise ValueError("only ledger observation subscription is allowed")


class XRPLReadOnlyWebSocketAdapter:
    def __init__(
        self,
        client,
        *,
        ledger_stream_name: str = "ledger",
        max_reconnects: int = 3,
        base_backoff_seconds: float = 1.0,
    ) -> None:
        self.client = client
        self.ledger_stream_name = ledger_stream_name
        self.max_reconnects = max(0, int(max_reconnects))
        self.base_backoff_seconds = non_negative_float(base_backoff_seconds, default=1.0)
        self.connected = False
        self.latest_ledger_index = 0
        self.latest_validated_ledger_index = 0
        self.reconnect_count = 0
        self.backoff_seconds = 0.0
        self.reason = "DISCONNECTED"

    def connect(self) -> bool:
        if self.reconnect_count >= self.max_reconnects and self.max_reconnects > 0:
            self.connected = False
            self.reason = "MAX_RECONNECTS_EXCEEDED"
            return False
        try:
            result = self.client.connect()
        except Exception:
            result = False
        self.connected = bool(result)
        if self.connected:
            self.reason = "CONNECTED"
            self.backoff_seconds = 0.0
            return True
        self.reconnect_count += 1
        self.backoff_seconds = self._next_backoff()
        self.reason = "CONNECT_FAILED"
        return False

    def subscribe_ledgers(self) -> bool:
        if not self.connected:
            return False
        command = {"command": "subscribe", "streams": [self.ledger_stream_name]}
        _validate_readonly_command(command)
        try:
            sender = getattr(self.client, "send", None)
            if sender is None:
                return False
            sender(command)
        except Exception:
            self.connected = False
            self.reason = "SUBSCRIBE_FAILED"
            return False
        self.reason = "SUBSCRIBED"
        return True

    def next_ledger_event(self) -> XRPLLedgerEvent | None:
        if not self.connected:
            self.reason = "DISCONNECTED"
            return None
        try:
            receiver = getattr(self.client, "receive", None)
            message = receiver() if receiver is not None else None
        except Exception:
            self.connected = False
            self.reason = "RECEIVE_FAILED"
            return None
        event = self._parse_ledger_event(message)
        if event is None:
            self.reason = "MALFORMED_LEDGER_EVENT"
            return None
        self.latest_ledger_index = max(self.latest_ledger_index, event.ledger_index)
        if event.validated:
            self.latest_validated_ledger_index = max(self.latest_validated_ledger_index, event.ledger_index)
        self.reason = "LEDGER_EVENT"
        return event

    def health(self) -> XRPLIngestionHealth:
        return XRPLIngestionHealth(
            connected=self.connected,
            latest_ledger_index=self.latest_ledger_index,
            latest_validated_ledger_index=self.latest_validated_ledger_index,
            reconnect_count=self.reconnect_count,
            backoff_seconds=self.backoff_seconds,
            reason=self.reason,
        )

    def close(self) -> None:
        closer = getattr(self.client, "close", None)
        if closer is not None:
            try:
                closer()
            except Exception:
                pass
        self.connected = False
        self.reason = "CLOSED"

    def _next_backoff(self) -> float:
        exponent = max(0, self.reconnect_count - 1)
        return min(60.0, self.base_backoff_seconds * (2**exponent))

    def _parse_ledger_event(self, message: object) -> XRPLLedgerEvent | None:
        if not isinstance(message, dict):
            return None
        ledger_index = non_negative_int(
            message.get("ledger_index", message.get("ledger_indexvalidated", message.get("ledger_index_closed", 0)))
        )
        if ledger_index <= 0:
            return None
        close_time: datetime | None = utc_or_none(message.get("close_time_iso") or message.get("close_time"))
        validated = bool(message.get("validated", message.get("type") == "ledgerClosed"))
        return XRPLLedgerEvent(
            ledger_index=ledger_index,
            ledger_hash=None if message.get("ledger_hash") is None else str(message.get("ledger_hash")),
            close_time=close_time,
            validated=validated,
            raw=message,
        )
