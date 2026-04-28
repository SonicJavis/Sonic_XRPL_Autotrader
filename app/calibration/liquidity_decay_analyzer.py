from __future__ import annotations

from dataclasses import dataclass

from app.db.models import XRPLOrderbookSnapshot


@dataclass(slots=True)
class LiquidityDecayResult:
    depth_loss_rate: float
    spread_expansion_rate: float
    level_removal_frequency: float
    decay_score: float
    collapse_events: int


class LiquidityDecayAnalyzer:
    def analyze(self, snapshots: list[XRPLOrderbookSnapshot]) -> LiquidityDecayResult:
        if len(snapshots) < 2:
            return LiquidityDecayResult(
                depth_loss_rate=0.0,
                spread_expansion_rate=0.0,
                level_removal_frequency=0.0,
                decay_score=0.0,
                collapse_events=0,
            )

        ordered = sorted(snapshots, key=lambda s: s.ledger_index)
        for prev, curr in zip(ordered[:-1], ordered[1:]):
            if curr.ledger_index <= prev.ledger_index:
                raise ValueError("INVALID_LEDGER_ORDERING")

        total_depth_loss = 0.0
        spread_expansion = 0.0
        removal_hits = 0
        collapse_events = 0

        for prev, curr in zip(ordered[:-1], ordered[1:]):
            prev_depth = max(0.0, float(prev.bid_depth_xrp) + float(prev.ask_depth_xrp))
            curr_depth = max(0.0, float(curr.bid_depth_xrp) + float(curr.ask_depth_xrp))
            prev_spread = max(0.0, float(prev.spread_pct))
            curr_spread = max(0.0, float(curr.spread_pct))

            if prev_depth > 0:
                loss = max(0.0, (prev_depth - curr_depth) / prev_depth)
                total_depth_loss += loss
                if loss >= 0.35:
                    collapse_events += 1
                if loss >= 0.20:
                    removal_hits += 1

            if curr_spread > prev_spread:
                spread_expansion += (curr_spread - prev_spread)

        steps = max(1, len(ordered) - 1)
        depth_loss_rate = max(0.0, min(1.0, total_depth_loss / steps))
        spread_expansion_rate = max(0.0, min(1.0, (spread_expansion / steps) / 5.0))
        level_removal_frequency = max(0.0, min(1.0, removal_hits / steps))

        decay_score = max(
            0.0,
            min(
                1.0,
                (depth_loss_rate * 0.5)
                + (spread_expansion_rate * 0.3)
                + (level_removal_frequency * 0.2),
            ),
        )

        return LiquidityDecayResult(
            depth_loss_rate=depth_loss_rate,
            spread_expansion_rate=spread_expansion_rate,
            level_removal_frequency=level_removal_frequency,
            decay_score=decay_score,
            collapse_events=collapse_events,
        )
