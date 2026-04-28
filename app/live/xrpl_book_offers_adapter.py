from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite
from typing import Any

from app.live.xrpl_ingestion_models import (
    XRPLBookOfferSnapshot,
    XRPLIngestionHealth,
    XRPLLedgerEvent,
    non_negative_float,
    non_negative_int,
)


@dataclass(frozen=True, slots=True)
class XRPLWatchedTokenRef:
    token_id: int
    issuer: str
    currency: str
    is_xrp: bool = False


class XRPLBookOffersAdapter:
    def __init__(self, client, *, max_snapshot_age_ms: int = 15000) -> None:
        self.client = client
        self.max_snapshot_age_ms = max(1, int(max_snapshot_age_ms))
        self.last_snapshot_at: datetime | None = None
        self.stale_snapshot_count = 0
        self.rejected_snapshot_count = 0
        self.reason = "IDLE"

    def fetch_book_snapshot(
        self,
        token: XRPLWatchedTokenRef,
        ledger_event: XRPLLedgerEvent,
    ) -> XRPLBookOfferSnapshot | None:
        if ledger_event.ledger_index <= 0:
            self.rejected_snapshot_count += 1
            self.reason = "INVALID_LEDGER"
            return None
        response = self._request_books(token=token, ledger_index=ledger_event.ledger_index)
        if not isinstance(response, dict):
            self.rejected_snapshot_count += 1
            self.reason = "MALFORMED_BOOK_RESPONSE"
            return None
        response_ledger = non_negative_int(response.get("ledger_index", ledger_event.ledger_index))
        if abs(response_ledger - ledger_event.ledger_index) > 1:
            self.stale_snapshot_count += 1
            self.reason = "STALE_LEDGER_MISMATCH"
            return None
        bids = self._offers(response.get("bids", response.get("bid_offers", [])))
        asks = self._offers(response.get("asks", response.get("ask_offers", response.get("offers", []))))
        if not bids or not asks:
            self.rejected_snapshot_count += 1
            self.reason = "EMPTY_BOOK"
            return None
        best_bid = max(offer["price"] for offer in bids)
        best_ask = min(offer["price"] for offer in asks)
        if best_bid <= 0.0 or best_ask <= 0.0:
            self.rejected_snapshot_count += 1
            self.reason = "INVALID_PRICE"
            return None
        bid_depth = sum(offer["xrp_value"] for offer in bids if offer["price"] == best_bid)
        ask_depth = sum(offer["xrp_value"] for offer in asks if offer["price"] == best_ask)
        if bid_depth <= 0.0 or ask_depth <= 0.0:
            self.rejected_snapshot_count += 1
            self.reason = "NO_DEPTH"
            return None
        mid = max((best_bid + best_ask) / 2.0, 1e-9)
        spread_pct = max(0.0, ((best_ask - best_bid) / mid) * 100.0)
        now = ledger_event.close_time or datetime.fromtimestamp(0, tz=timezone.utc)
        self.last_snapshot_at = now
        self.reason = "SNAPSHOT_READY"
        return XRPLBookOfferSnapshot(
            token_id=token.token_id,
            issuer=token.issuer,
            currency=token.currency,
            ledger_index=response_ledger,
            best_bid=best_bid,
            best_ask=best_ask,
            bid_depth_xrp=bid_depth,
            ask_depth_xrp=ask_depth,
            spread_pct=spread_pct,
            observed_at=now,
            raw={"ledger_index": response_ledger},
        )

    def health(self) -> dict[str, object]:
        return XRPLIngestionHealth(
            connected=True,
            last_snapshot_at=self.last_snapshot_at,
            stale_snapshot_count=self.stale_snapshot_count,
            rejected_snapshot_count=self.rejected_snapshot_count,
            reason=self.reason,
        ).to_dict()

    def _request_books(self, *, token: XRPLWatchedTokenRef, ledger_index: int) -> dict[str, object] | None:
        request = getattr(self.client, "book_offers", None)
        if request is None:
            return None
        return request(token=token, ledger_index=ledger_index)

    def _offers(self, raw: object) -> list[dict[str, float]]:
        if not isinstance(raw, list):
            return []
        offers: list[dict[str, float]] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            price = non_negative_float(item.get("price", item.get("quality", 0.0)))
            amount = non_negative_float(item.get("amount", item.get("taker_gets", item.get("xrp_value", 0.0))))
            xrp_value = non_negative_float(item.get("xrp_value", amount * price))
            if price > 0.0 and xrp_value > 0.0 and isfinite(price) and isfinite(xrp_value):
                offers.append({"price": price, "xrp_value": xrp_value})
        return offers
