from __future__ import annotations

from datetime import datetime, timedelta, timezone
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
        snapshot_throttle_ms: int = 500,
        max_ledger_gap: int = 128,
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        self.ws_adapter = ws_adapter
        self.book_adapter = book_adapter
        self.watched_tokens_provider = watched_tokens_provider
        self.default_requested_size = max(0.0, float(default_requested_size))
        self.max_snapshot_age_ms = max(1, int(max_snapshot_age_ms))
        self.snapshot_throttle_ms = max(0, int(snapshot_throttle_ms))
        self.max_ledger_gap = max(1, int(max_ledger_gap))
        self.now_provider = now_provider or (lambda: datetime.now(tz=timezone.utc))
        self.stale_snapshot_count = 0
        self.rejected_snapshot_count = 0
        self.ledger_gap_count = 0
        self.duplicate_ledger_count = 0
        self.throttled_snapshot_count = 0
        self.snapshot_count = 0
        self.unfunded_liquidity_estimate = 0.0
        self.last_snapshot_latency_ms = 0.0
        self._first_snapshot_at: datetime | None = None
        self._last_snapshot_at: datetime | None = None
        self._tokens: list[XRPLWatchedTokenRef] = []
        self._token_index = 0
        self._last_ledger_index = 0
        self._last_snapshot_ledger_index = 0
        self.reason = "IDLE"

    def next_snapshot(self) -> ShadowSnapshotInput | None:
        ledger = self.ws_adapter.next_ledger_event()
        if ledger is None:
            self.reason = "NO_LEDGER_EVENT"
            return None
        if not ledger.validated:
            self.rejected_snapshot_count += 1
            self.reason = "UNVALIDATED_LEDGER"
            return None
        if ledger.ledger_index < self._last_ledger_index:
            self.rejected_snapshot_count += 1
            self.reason = "LEDGER_REGRESSION"
            return None
        if ledger.ledger_index == self._last_snapshot_ledger_index:
            self.duplicate_ledger_count += 1
            self.reason = "DUPLICATE_LEDGER_IGNORED"
            return None
        if self._last_ledger_index and ledger.ledger_index - self._last_ledger_index > self.max_ledger_gap:
            self.stale_snapshot_count += 1
            self.ledger_gap_count += 1
            self.reason = "LEDGER_GAP"
            self._last_ledger_index = ledger.ledger_index
            return None
        now = ledger.close_time or _deterministic_ledger_time(ledger.ledger_index)
        if self._last_snapshot_at is not None:
            elapsed_ms = max(0.0, (now - self._last_snapshot_at).total_seconds() * 1000.0)
            if elapsed_ms < self.snapshot_throttle_ms:
                self.throttled_snapshot_count += 1
                self.reason = "SNAPSHOT_THROTTLED"
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
        age_reference = ledger.close_time or book.observed_at
        if (age_reference - book.observed_at).total_seconds() * 1000.0 > self.max_snapshot_age_ms:
            self.stale_snapshot_count += 1
            self.reason = "STALE_SNAPSHOT_AGE"
            return None
        side_depth = min(book.bid_depth_xrp, book.ask_depth_xrp)
        observed_possible_fill = min(self.default_requested_size, side_depth)
        if side_depth <= 0.0 or observed_possible_fill <= 0.0:
            self.rejected_snapshot_count += 1
            self.reason = "NO_CONSERVATIVE_LIQUIDITY"
            return None
        pessimistic_price = max(book.best_ask, book.best_bid)
        slippage_estimate = max(0.0, book.spread_pct / 100.0)
        route_instability = 0.25
        competition_penalty = 0.25
        if book.spread_pct > 8.0:
            route_instability = min(1.0, route_instability + 0.20)
            competition_penalty = min(1.0, competition_penalty + 0.10)
        if side_depth <= self.default_requested_size * 0.25:
            route_instability = min(1.0, route_instability + 0.15)
            competition_penalty = min(1.0, competition_penalty + 0.15)
        imbalance = abs(book.bid_depth_xrp - book.ask_depth_xrp) / max(book.bid_depth_xrp + book.ask_depth_xrp, 1e-9)
        if imbalance >= 0.75:
            route_instability = min(1.0, route_instability + 0.15)
            competition_penalty = min(1.0, competition_penalty + 0.10)
        self._last_snapshot_ledger_index = ledger.ledger_index
        self._last_snapshot_at = now
        if self._first_snapshot_at is None:
            self._first_snapshot_at = now
        self.snapshot_count += 1
        self.unfunded_liquidity_estimate += max(0.0, side_depth - observed_possible_fill)
        self.last_snapshot_latency_ms = max(0.0, (age_reference - book.observed_at).total_seconds() * 1000.0)
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
            route_instability=route_instability,
            competition_penalty=competition_penalty,
            slippage_estimate=slippage_estimate,
            observed_at=book.observed_at,
            snapshot_quality_score=max(0.0, min(1.0, 1.0 - (book.spread_pct / 100.0))),
            ledger_latency_proxy=self.last_snapshot_latency_ms,
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
            snapshot_rate_per_sec=self._snapshot_rate(),
            snapshot_count=self.snapshot_count,
            last_snapshot_latency_ms=self.last_snapshot_latency_ms,
            ledger_gap_detected=self.ledger_gap_count > 0,
            ledger_gap_count=self.ledger_gap_count,
            duplicate_ledger_count=self.duplicate_ledger_count,
            throttled_snapshot_count=self.throttled_snapshot_count,
            unfunded_liquidity_estimate=self.unfunded_liquidity_estimate,
            snapshot_rejection_rate=self._rejection_rate(),
            xrpl_warning=XRPL_INGESTION_WARNING,
        )

    def _snapshot_rate(self) -> float:
        if self._first_snapshot_at is None or self._last_snapshot_at is None or self.snapshot_count <= 0:
            return 0.0
        elapsed = max((self._last_snapshot_at - self._first_snapshot_at).total_seconds(), 1.0)
        return round(self.snapshot_count / elapsed, 6)

    def _rejection_rate(self) -> float:
        rejected = (
            self.rejected_snapshot_count
            + self.stale_snapshot_count
            + self.duplicate_ledger_count
            + self.throttled_snapshot_count
            + self.book_adapter.rejected_snapshot_count
            + self.book_adapter.stale_snapshot_count
        )
        total = rejected + self.snapshot_count
        return 0.0 if total <= 0 else round(rejected / total, 6)

    def _next_token(self) -> XRPLWatchedTokenRef | None:
        if not self._tokens:
            self._tokens = list(self.watched_tokens_provider())
        if not self._tokens:
            return None
        token = self._tokens[self._token_index % len(self._tokens)]
        self._token_index += 1
        return token


def _deterministic_ledger_time(ledger_index: int) -> datetime:
    return datetime.fromtimestamp(0, tz=timezone.utc) + timedelta(seconds=max(0, int(ledger_index)) * 4)
