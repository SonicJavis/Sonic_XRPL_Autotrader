from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.db.models import XRPLOrderbookSequence, XRPLOrderbookSnapshot


def _utc(ts: datetime) -> datetime:
    if ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


@dataclass(slots=True)
class SequenceMetrics:
    decay_score: float
    volatility_score: float
    collapse_events: int
    duration_ms: int


def compute_sequence_metrics(snapshots: list[XRPLOrderbookSnapshot]) -> SequenceMetrics:
    if len(snapshots) < 2:
        return SequenceMetrics(decay_score=0.0, volatility_score=0.0, collapse_events=0, duration_ms=0)

    ordered = sorted(snapshots, key=lambda s: s.ledger_index)
    start = _utc(ordered[0].observed_at)
    end = _utc(ordered[-1].observed_at)
    duration_ms = max(0, int((end - start).total_seconds() * 1000.0))

    total_depth_loss = 0.0
    spread_moves = 0.0
    collapse_events = 0

    for prev, curr in zip(ordered[:-1], ordered[1:]):
        prev_depth = max(0.0, float(prev.bid_depth_xrp) + float(prev.ask_depth_xrp))
        curr_depth = max(0.0, float(curr.bid_depth_xrp) + float(curr.ask_depth_xrp))
        if prev_depth > 0:
            depth_drop = max(0.0, (prev_depth - curr_depth) / prev_depth)
            total_depth_loss += depth_drop
            if depth_drop >= 0.35:
                collapse_events += 1

        prev_spread = max(0.0, float(prev.spread_pct))
        curr_spread = max(0.0, float(curr.spread_pct))
        spread_moves += abs(curr_spread - prev_spread)

    steps = max(1, len(ordered) - 1)
    avg_depth_loss = total_depth_loss / steps
    avg_spread_move = spread_moves / steps

    decay_score = max(0.0, min(1.0, (avg_depth_loss * 0.7) + min(1.0, avg_spread_move / 10.0) * 0.3))
    volatility_score = max(0.0, min(1.0, avg_spread_move / 8.0))

    return SequenceMetrics(
        decay_score=decay_score,
        volatility_score=volatility_score,
        collapse_events=collapse_events,
        duration_ms=duration_ms,
    )


def build_sequence(token_id: int, snapshots: list[XRPLOrderbookSnapshot]) -> XRPLOrderbookSequence:
    if not snapshots:
        raise ValueError("NO_SNAPSHOTS")

    ordered = sorted(snapshots, key=lambda s: s.ledger_index)
    for prev, curr in zip(ordered[:-1], ordered[1:]):
        if curr.ledger_index <= prev.ledger_index:
            raise ValueError("INVALID_LEDGER_ORDERING")
        if curr.token_id != token_id or prev.token_id != token_id:
            raise ValueError("MIXED_TOKEN_SEQUENCE")

    metrics = compute_sequence_metrics(ordered)
    return XRPLOrderbookSequence(
        token_id=token_id,
        start_ledger=int(ordered[0].ledger_index),
        end_ledger=int(ordered[-1].ledger_index),
        snapshot_count=len(ordered),
        duration_ms=metrics.duration_ms,
        decay_score=metrics.decay_score,
        volatility_score=metrics.volatility_score,
        collapse_events=metrics.collapse_events,
    )
