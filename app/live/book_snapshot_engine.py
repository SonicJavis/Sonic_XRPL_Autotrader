from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol

from app.market_data.snapshot_builder import build_snapshot_from_offers


def _utc(ts: datetime | None = None) -> datetime:
    if ts is None:
        return datetime.now(tz=timezone.utc)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


class BookOffersClient(Protocol):
    def get_book_offers(self, taker_gets: dict[str, Any] | str, taker_pays: dict[str, Any] | str) -> dict[str, Any]: ...


@dataclass(slots=True)
class BookSnapshotRequest:
    token_key: str
    taker_gets: dict[str, Any] | str
    taker_pays: dict[str, Any] | str


@dataclass(slots=True)
class BookSnapshotDiff:
    best_bid_changed: bool
    best_ask_changed: bool
    bid_depth_delta_xrp: float
    ask_depth_delta_xrp: float
    liquidity_delta_xrp: float
    offer_count_delta: int


@dataclass(slots=True)
class PulledBookSnapshot:
    token_key: str
    ledger_index: int
    trigger: str
    observed_at: datetime
    snapshot_age_ms: int
    possibly_stale: bool
    best_bid: float | None
    best_ask: float | None
    bid_depth_xrp: float
    ask_depth_xrp: float
    liquidity_xrp: float
    order_count: int
    raw_offer_count: int
    valid: bool
    invalid_reasons: list[str] = field(default_factory=list)
    diff: BookSnapshotDiff | None = None
    parsed: dict[str, Any] = field(default_factory=dict)


class BookSnapshotEngine:
    def __init__(self, client: BookOffersClient, *, fallback_interval_ms: int = 1500, stale_after_ms: int = 2000) -> None:
        self.client = client
        self.fallback_interval_ms = max(1, int(fallback_interval_ms))
        self.stale_after_ms = max(1, int(stale_after_ms))
        self._last_snapshot_by_token: dict[str, PulledBookSnapshot] = {}

    def should_pull(
        self,
        *,
        token_key: str,
        ledger_index: int,
        now: datetime,
        force_interval_fallback: bool = False,
    ) -> tuple[bool, str]:
        now_utc = _utc(now)
        previous = self._last_snapshot_by_token.get(token_key)
        if previous is None:
            return True, "bootstrap"
        if ledger_index > previous.ledger_index:
            return True, "new_ledger"
        age_ms = int((now_utc - previous.observed_at).total_seconds() * 1000.0)
        if force_interval_fallback or age_ms >= self.fallback_interval_ms:
            return True, "interval_fallback"
        return False, "cached"

    def pull_snapshot(
        self,
        *,
        request: BookSnapshotRequest,
        ledger_index: int,
        now: datetime,
        force_interval_fallback: bool = False,
    ) -> PulledBookSnapshot:
        should_pull, trigger = self.should_pull(
            token_key=request.token_key,
            ledger_index=ledger_index,
            now=now,
            force_interval_fallback=force_interval_fallback,
        )
        now_utc = _utc(now)
        previous = self._last_snapshot_by_token.get(request.token_key)

        if not should_pull and previous is not None:
            age_ms = int((now_utc - previous.observed_at).total_seconds() * 1000.0)
            return PulledBookSnapshot(
                token_key=previous.token_key,
                ledger_index=previous.ledger_index,
                trigger=trigger,
                observed_at=previous.observed_at,
                snapshot_age_ms=max(0, age_ms),
                possibly_stale=age_ms >= self.stale_after_ms,
                best_bid=previous.best_bid,
                best_ask=previous.best_ask,
                bid_depth_xrp=previous.bid_depth_xrp,
                ask_depth_xrp=previous.ask_depth_xrp,
                liquidity_xrp=previous.liquidity_xrp,
                order_count=previous.order_count,
                raw_offer_count=previous.raw_offer_count,
                valid=previous.valid,
                invalid_reasons=list(previous.invalid_reasons),
                diff=previous.diff,
                parsed=dict(previous.parsed),
            )

        result = self.client.get_book_offers(request.taker_gets, request.taker_pays)
        offers = list(result.get("offers", []))
        built = build_snapshot_from_offers(offers)
        parsed = dict(built.get("parsed", {}))
        diff = self._build_diff(previous=previous, current=built)
        snapshot = PulledBookSnapshot(
            token_key=request.token_key,
            ledger_index=int(ledger_index),
            trigger=trigger,
            observed_at=now_utc,
            snapshot_age_ms=0,
            possibly_stale=False,
            best_bid=(parsed.get("best_bid") or {}).get("price") if parsed.get("best_bid") else None,
            best_ask=(parsed.get("best_ask") or {}).get("price") if parsed.get("best_ask") else None,
            bid_depth_xrp=float(built.get("liquidity_bid_xrp", 0.0)),
            ask_depth_xrp=float(built.get("liquidity_ask_xrp", 0.0)),
            liquidity_xrp=float(built.get("liquidity_xrp", 0.0)),
            order_count=int(built.get("order_count", 0)),
            raw_offer_count=int(built.get("raw_offer_count", 0)),
            valid=bool(built.get("valid", False)),
            invalid_reasons=list(built.get("invalid_reasons", [])),
            diff=diff,
            parsed=parsed,
        )
        self._last_snapshot_by_token[request.token_key] = snapshot
        return snapshot

    @staticmethod
    def _build_diff(previous: PulledBookSnapshot | None, current: dict[str, Any]) -> BookSnapshotDiff | None:
        if previous is None:
            return None

        parsed = dict(current.get("parsed", {}))
        best_bid = (parsed.get("best_bid") or {}).get("price") if parsed.get("best_bid") else None
        best_ask = (parsed.get("best_ask") or {}).get("price") if parsed.get("best_ask") else None
        bid_depth = float(current.get("liquidity_bid_xrp", 0.0))
        ask_depth = float(current.get("liquidity_ask_xrp", 0.0))
        liquidity = float(current.get("liquidity_xrp", 0.0))
        order_count = int(current.get("order_count", 0))

        return BookSnapshotDiff(
            best_bid_changed=best_bid != previous.best_bid,
            best_ask_changed=best_ask != previous.best_ask,
            bid_depth_delta_xrp=round(bid_depth - previous.bid_depth_xrp, 6),
            ask_depth_delta_xrp=round(ask_depth - previous.ask_depth_xrp, 6),
            liquidity_delta_xrp=round(liquidity - previous.liquidity_xrp, 6),
            offer_count_delta=order_count - previous.order_count,
        )