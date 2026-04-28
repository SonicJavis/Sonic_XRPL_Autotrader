from __future__ import annotations

from itertools import cycle
from math import isfinite
from typing import Callable, Iterable

from app.live.shadow_snapshot_source import ShadowSnapshotInput, ShadowSnapshotSource
from app.live.xrpl_book_offers_adapter import XRPLBookOffersAdapter, XRPLWatchedTokenRef
from app.live.xrpl_ingestion_models import XRPLIngestionHealth, XRPL_INGESTION_WARNING, non_negative_float
from app.live.xrpl_readonly_ws_adapter import XRPLReadOnlyWebSocketAdapter


class XRPLWebSocketSnapshotSource:
    def __init__(
        self,
        *,
        ws_adapter: XRPLReadOnlyWebSocketAdapter,
        book_adapter: XRPLBookOffersAdapter,
        watched_tokens_provider: Callable[[], Iterable[XRPLWatchedTokenRef]],
        default_requested_size: float = 100.0,
        max_snapshot_age_ms: int = 15000,
    ) -> None:
        self.ws_adapter = ws_adapter
        self.book_adapter = book_adapter
        self.watched_tokens_provider = watched_tokens_provider
        self.default_requested_size = max(0.0, float(default_requested_size))
        self.max_snapshot_age_ms = max(1, int(max_snapshot_age_ms))
        self.stale_snapshot_count = 0
        self.rejected_snapshot_count = 0
        self._tokens: list[XRPLWatchedTokenRef] = []
        self._token_index = 0
        self._last_ledger_index = 0
        self.reason = "IDLE"

    def next_snapshot(self) -> ShadowSnapshotInput | None:
        ledger = self.ws_adapter.next_ledger_event()
        if ledger is None:
            self.reason = "NO_LEDGER_EVENT"
            return None
        if ledger.ledger_index < self._last_ledger_index:
            self.rejected_snapshot_count += 1
            self.reason = "LEDGER_REGRESSION"
            return None
        if self._last_ledger_index and ledger.ledger_index - self._last_ledger_index > 128:
            self.stale_snapshot_count += 1
            self.reason = "LEDGER_GAP"
            self._last_ledger_index = ledger.ledger_index
            return None
        self._last_ledger_index = ledger.ledger_index
        token = self._next_token()
        if token is None:
            self.reason = "NO_WATCHED_TOKEN"
            return None
        book = self.book_adapter.fetch_book_snapshot(token, ledger)
        if book is None:
            self.rejected_snapshot_count += 1
            self.reason = self.book_adapter.reason
            return None
        if book.ledger_index < ledger.ledger_index - 1:
            self.stale_snapshot_count += 1
            self.reason = "STALE_BOOK_SNAPSHOT"
            return None
        side_depth = min(book.bid_depth_xrp, book.ask_depth_xrp)
        observed_possible_fill = min(self.default_requested_size, side_depth)
        if side_depth <= 0.0 or observed_possible_fill <= 0.0:
            self.rejected_snapshot_count += 1
            self.reason = "NO_CONSERVATIVE_LIQUIDITY"
            return None
        pessimistic_price = max(book.best_ask, book.best_bid)
        slippage_estimate = max(0.0, book.spread_pct / 100.0)
        self.reason = "SNAPSHOT_READY"
        return ShadowSnapshotInput(
            token_id=book.token_id,
            issuer=book.issuer,
            currency=book.currency,
            ledger_index=ledger.ledger_index if ledger.validated else book.ledger_index,
            snapshot_price=pessimistic_price,
            execution_price_proxy=pessimistic_price,
            requested_size=self.default_requested_size,
            snapshot_derived_liquidity=side_depth,
            observed_possible_fill=min(observed_possible_fill, side_depth),
            path_complexity=1,
            route_instability=0.25,
            competition_penalty=0.25,
            slippage_estimate=slippage_estimate,
            observed_at=book.observed_at,
        )

    def health(self) -> XRPLIngestionHealth:
        ws = self.ws_adapter.health()
        return XRPLIngestionHealth(
            connected=ws.connected,
            latest_ledger_index=ws.latest_ledger_index,
            latest_validated_ledger_index=ws.latest_validated_ledger_index,
            last_snapshot_at=self.book_adapter.last_snapshot_at,
            stale_snapshot_count=self.stale_snapshot_count + self.book_adapter.stale_snapshot_count,
            rejected_snapshot_count=self.rejected_snapshot_count + self.book_adapter.rejected_snapshot_count,
            reconnect_count=ws.reconnect_count,
            backoff_seconds=ws.backoff_seconds,
            reason=self.reason,
            xrpl_warning=XRPL_INGESTION_WARNING,
        )

    def _next_token(self) -> XRPLWatchedTokenRef | None:
        if not self._tokens:
            self._tokens = list(self.watched_tokens_provider())
        if not self._tokens:
            return None
        token = self._tokens[self._token_index % len(self._tokens)]
        self._token_index += 1
        return token
