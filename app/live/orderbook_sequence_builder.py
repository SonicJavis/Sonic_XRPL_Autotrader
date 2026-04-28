from __future__ import annotations

from dataclasses import dataclass

from app.calibration.time_series import build_sequence
from app.db.models import XRPLOrderbookSequence, XRPLOrderbookSnapshot
from app.live.book_snapshot_engine import PulledBookSnapshot


@dataclass(slots=True)
class LiveOrderbookSequence:
    sequence: XRPLOrderbookSequence
    snapshots: list[XRPLOrderbookSnapshot]
    depth_persistence: float
    top_of_book_churn: float
    liquidity_disappearance_rate: float
    fake_wall_risk: float
    flicker_risk: float
    missing_ledgers: int
    warnings: list[str]


class OrderbookSequenceBuilder:
    def build(self, *, token_id: int, pulled_snapshots: list[PulledBookSnapshot]) -> LiveOrderbookSequence:
        if not pulled_snapshots:
            raise ValueError("NO_SNAPSHOTS")

        ordered = sorted(pulled_snapshots, key=lambda snap: snap.ledger_index)
        for prev, curr in zip(ordered[:-1], ordered[1:]):
            if curr.ledger_index <= prev.ledger_index:
                raise ValueError("INVALID_LEDGER_ORDERING")

        db_snapshots = [self._to_db_snapshot(token_id=token_id, pulled=snapshot) for snapshot in ordered]
        sequence = build_sequence(token_id, db_snapshots)

        transitions = max(1, len(ordered) - 1)
        persistence_scores: list[float] = []
        top_of_book_changes = 0
        disappearance_events = 0
        fake_wall_events = 0
        flicker_events = 0
        missing_ledgers = 0

        for prev, curr in zip(ordered[:-1], ordered[1:]):
            ledger_gap = max(0, int(curr.ledger_index) - int(prev.ledger_index) - 1)
            missing_ledgers += ledger_gap

            prev_depth = max(0.0, prev.bid_depth_xrp + prev.ask_depth_xrp)
            curr_depth = max(0.0, curr.bid_depth_xrp + curr.ask_depth_xrp)
            if prev_depth > 0:
                persistence_scores.append(max(0.0, min(1.0, curr_depth / prev_depth)))
                if curr_depth <= prev_depth * 0.45:
                    disappearance_events += 1
            else:
                persistence_scores.append(0.0)

            if prev.best_bid != curr.best_bid or prev.best_ask != curr.best_ask:
                top_of_book_changes += 1

            if prev.ask_depth_xrp > 0 and curr.ask_depth_xrp > 0:
                wall_ratio = curr.ask_depth_xrp / prev.ask_depth_xrp
                if prev.ask_depth_xrp >= 250.0 and wall_ratio <= 0.30:
                    fake_wall_events += 1
            if prev.bid_depth_xrp > 0 and curr.bid_depth_xrp > 0:
                wall_ratio = curr.bid_depth_xrp / prev.bid_depth_xrp
                if prev.bid_depth_xrp >= 250.0 and wall_ratio <= 0.30:
                    fake_wall_events += 1

            if prev.valid and curr.valid and (prev.diff or curr.diff):
                offer_delta = abs((curr.diff.offer_count_delta if curr.diff is not None else 0))
                liquidity_delta = abs((curr.diff.liquidity_delta_xrp if curr.diff is not None else 0.0))
                if offer_delta >= 2 or liquidity_delta >= max(120.0, prev_depth * 0.25):
                    flicker_events += 1

        depth_persistence = sum(persistence_scores) / max(1, len(persistence_scores))
        top_of_book_churn = top_of_book_changes / transitions
        liquidity_disappearance_rate = disappearance_events / transitions
        fake_wall_risk = fake_wall_events / transitions
        flicker_risk = flicker_events / transitions

        warnings: list[str] = []
        if liquidity_disappearance_rate >= 0.30:
            warnings.append("disappearing_liquidity")
        if fake_wall_risk >= 0.25:
            warnings.append("fake_walls")
        if flicker_risk >= 0.25:
            warnings.append("flicker")
        if missing_ledgers > 0:
            warnings.append("missing_ledgers")

        return LiveOrderbookSequence(
            sequence=sequence,
            snapshots=db_snapshots,
            depth_persistence=round(depth_persistence, 6),
            top_of_book_churn=round(top_of_book_churn, 6),
            liquidity_disappearance_rate=round(liquidity_disappearance_rate, 6),
            fake_wall_risk=round(fake_wall_risk, 6),
            flicker_risk=round(flicker_risk, 6),
            missing_ledgers=missing_ledgers,
            warnings=warnings,
        )

    @staticmethod
    def _to_db_snapshot(*, token_id: int, pulled: PulledBookSnapshot) -> XRPLOrderbookSnapshot:
        return XRPLOrderbookSnapshot(
            token_id=token_id,
            ledger_index=int(pulled.ledger_index),
            best_bid=float(pulled.best_bid or 0.0),
            best_ask=float(pulled.best_ask or 0.0),
            bid_depth_xrp=float(pulled.bid_depth_xrp),
            ask_depth_xrp=float(pulled.ask_depth_xrp),
            spread_pct=0.0
            if not pulled.best_bid or not pulled.best_ask or pulled.best_ask <= 0
            else max(0.0, ((float(pulled.best_ask) - float(pulled.best_bid)) / float(pulled.best_ask)) * 100.0),
            levels_json=[],
            observed_at=pulled.observed_at,
        )