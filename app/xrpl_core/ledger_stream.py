from __future__ import annotations


class LedgerStreamClient:
    """WebSocket stream placeholder for future ledger subscriptions."""

    def __init__(self, ws_url: str) -> None:
        self.ws_url = ws_url
        self.subscribed_streams: list[str] = []

    def subscribe_ledger_stream(self) -> dict[str, object]:
        if "ledger" not in self.subscribed_streams:
            self.subscribed_streams.append("ledger")
        return {"ok": True, "ws_url": self.ws_url, "streams": list(self.subscribed_streams)}
