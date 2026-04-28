from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


@dataclass(slots=True)
class XRPLWebSocketEvent:
    event_type: str
    ledger_index: int | None
    ledger_closed: bool
    received_at: datetime = field(default_factory=_utcnow)
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class XRPLWebSocketHealth:
    connected: bool
    reconnect_count: int
    last_ledger_index: int | None
    last_ledger_close_at: datetime | None
    missed_ledger_gaps: int
    subscriptions: tuple[str, ...]


class XRPLWebSocketClient:
    """Ledger-oriented XRPL websocket client model for shadow-mode observation only."""

    DEFAULT_STREAMS: tuple[str, ...] = ("ledger", "validations")

    def __init__(
        self,
        ws_url: str,
        *,
        include_transactions: bool = False,
        max_reconnect_attempts: int = 3,
    ) -> None:
        self.ws_url = ws_url
        self.include_transactions = include_transactions
        self.max_reconnect_attempts = max(1, int(max_reconnect_attempts))
        self.connected = False
        self.reconnect_count = 0
        self.last_ledger_index: int | None = None
        self.last_ledger_close_at: datetime | None = None
        self.missed_ledger_gaps = 0
        self.last_error: str | None = None
        self._events: list[XRPLWebSocketEvent] = []

    @property
    def subscribed_streams(self) -> tuple[str, ...]:
        if self.include_transactions:
            return self.DEFAULT_STREAMS + ("transactions",)
        return self.DEFAULT_STREAMS

    def connect(self) -> dict[str, Any]:
        self.connected = True
        self.last_error = None
        return {
            "command": "subscribe",
            "streams": list(self.subscribed_streams),
            "ws_url": self.ws_url,
            "mode": "read_only_shadow",
        }

    def disconnect(self, reason: str | None = None) -> None:
        self.connected = False
        self.last_error = reason

    def reconnect(self) -> dict[str, Any]:
        self.reconnect_count = min(self.max_reconnect_attempts, self.reconnect_count + 1)
        self.connected = True
        return self.connect()

    def handle_disconnect(self, reason: str | None = None) -> dict[str, Any] | None:
        self.disconnect(reason)
        if self.reconnect_count >= self.max_reconnect_attempts:
            return None
        return self.reconnect()

    def handle_message(self, message: dict[str, Any]) -> XRPLWebSocketEvent | None:
        event_type = str(message.get("type") or message.get("stream") or "unknown")
        ledger_index = self._extract_ledger_index(message)
        ledger_closed = self._is_ledger_close_event(event_type=event_type, message=message)

        if ledger_closed and ledger_index is not None and self.last_ledger_index is not None and ledger_index > self.last_ledger_index + 1:
            self.missed_ledger_gaps += ledger_index - self.last_ledger_index - 1

        event = XRPLWebSocketEvent(
            event_type=event_type,
            ledger_index=ledger_index,
            ledger_closed=ledger_closed,
            payload=dict(message),
        )

        if ledger_closed and ledger_index is not None:
            self.last_ledger_index = ledger_index
            self.last_ledger_close_at = event.received_at

        self._events.append(event)
        return event

    def drain_events(self) -> list[XRPLWebSocketEvent]:
        events = list(self._events)
        self._events.clear()
        return events

    def health(self) -> XRPLWebSocketHealth:
        return XRPLWebSocketHealth(
            connected=self.connected,
            reconnect_count=self.reconnect_count,
            last_ledger_index=self.last_ledger_index,
            last_ledger_close_at=self.last_ledger_close_at,
            missed_ledger_gaps=self.missed_ledger_gaps,
            subscriptions=self.subscribed_streams,
        )

    @staticmethod
    def _extract_ledger_index(message: dict[str, Any]) -> int | None:
        candidates = [
            message.get("ledger_index"),
            message.get("ledger_index_max"),
            message.get("ledger"),
            message.get("validated_ledger_index"),
        ]
        ledger = message.get("ledger")
        if isinstance(ledger, dict):
            candidates.extend([ledger.get("ledger_index"), ledger.get("seq")])
        for candidate in candidates:
            if candidate is None:
                continue
            try:
                return int(candidate)
            except (TypeError, ValueError):
                continue
        return None

    @staticmethod
    def _is_ledger_close_event(*, event_type: str, message: dict[str, Any]) -> bool:
        if event_type == "ledgerClosed":
            return True
        if event_type == "ledger":
            return bool(message.get("ledger_index") is not None)
        if event_type == "validationReceived":
            return bool(message.get("validated_ledgers") or message.get("ledger_index"))
        return False