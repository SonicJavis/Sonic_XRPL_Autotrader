from __future__ import annotations

from dataclasses import dataclass

from app.db.models import XRPLOrderbookSnapshot


@dataclass(slots=True)
class FundednessProxyResult:
    fundedness_confidence: float
    wall_flicker_rate: float
    persistence_consistency: float
    unfilled_wall_rate: float


class FundednessProxy:
    def evaluate(self, snapshots: list[XRPLOrderbookSnapshot]) -> FundednessProxyResult:
        if len(snapshots) < 2:
            return FundednessProxyResult(
                fundedness_confidence=0.0,
                wall_flicker_rate=1.0,
                persistence_consistency=0.0,
                unfilled_wall_rate=1.0,
            )

        ordered = sorted(snapshots, key=lambda s: s.ledger_index)
        top_depths = [max(0.0, min(float(s.bid_depth_xrp), float(s.ask_depth_xrp))) for s in ordered]

        flickers = 0
        persistence_hits = 0
        unfilled_wall_hits = 0

        for prev, curr in zip(top_depths[:-1], top_depths[1:]):
            if prev > 0 and curr <= prev * 0.25:
                flickers += 1
            if prev > 0 and abs(curr - prev) / prev <= 0.12:
                persistence_hits += 1

            if prev >= 800.0 and curr >= 780.0:
                unfilled_wall_hits += 1

        steps = max(1, len(top_depths) - 1)
        wall_flicker_rate = max(0.0, min(1.0, flickers / steps))
        persistence_consistency = max(0.0, min(1.0, persistence_hits / steps))
        unfilled_wall_rate = max(0.0, min(1.0, unfilled_wall_hits / steps))

        fundedness_confidence = max(
            0.0,
            min(
                1.0,
                (persistence_consistency * 0.65)
                + ((1.0 - wall_flicker_rate) * 0.25)
                + ((1.0 - unfilled_wall_rate) * 0.10),
            ),
        )

        return FundednessProxyResult(
            fundedness_confidence=fundedness_confidence,
            wall_flicker_rate=wall_flicker_rate,
            persistence_consistency=persistence_consistency,
            unfilled_wall_rate=unfilled_wall_rate,
        )
