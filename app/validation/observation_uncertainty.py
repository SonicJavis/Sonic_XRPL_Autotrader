from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ObservationSample:
    bid_depth_xrp: float
    ask_depth_xrp: float
    spread_pct: float
    best_bid: float
    best_ask: float
    implied_mid_price: float


@dataclass(slots=True)
class ObservationUncertaintyResult:
    depth_reliability_score: float
    path_distortion_risk: float
    fundedness_uncertainty: float
    observation_confidence: float


class ObservationUncertaintyModel:
    def evaluate(self, samples: list[ObservationSample]) -> ObservationUncertaintyResult:
        if not samples:
            return ObservationUncertaintyResult(
                depth_reliability_score=0.0,
                path_distortion_risk=1.0,
                fundedness_uncertainty=1.0,
                observation_confidence=0.01,
            )

        total_depths = [max(0.0, float(s.bid_depth_xrp) + float(s.ask_depth_xrp)) for s in samples]
        spreads = [max(0.0, float(s.spread_pct)) for s in samples]

        flickers = 0
        persistence_hits = 0
        disappearing_top_hits = 0
        wall_nonfill_hits = 0
        inversions = 0
        implied_inconsistency = 0

        for prev, curr in zip(samples[:-1], samples[1:]):
            prev_depth = max(0.0, float(prev.bid_depth_xrp) + float(prev.ask_depth_xrp))
            curr_depth = max(0.0, float(curr.bid_depth_xrp) + float(curr.ask_depth_xrp))

            if prev_depth > 0 and curr_depth <= prev_depth * 0.4:
                flickers += 1
            if prev_depth > 0 and abs(curr_depth - prev_depth) / prev_depth <= 0.15:
                persistence_hits += 1

            prev_top = min(max(0.0, float(prev.bid_depth_xrp)), max(0.0, float(prev.ask_depth_xrp)))
            curr_top = min(max(0.0, float(curr.bid_depth_xrp)), max(0.0, float(curr.ask_depth_xrp)))
            if prev_top > 0 and curr_top <= prev_top * 0.3:
                disappearing_top_hits += 1

            if prev_top >= 700.0 and curr_top >= 680.0:
                wall_nonfill_hits += 1

            if float(curr.best_bid) > float(curr.best_ask):
                inversions += 1

            mid = (float(curr.best_bid) + float(curr.best_ask)) / 2.0 if (curr.best_bid > 0 and curr.best_ask > 0) else 0.0
            if mid > 0:
                diff = abs(float(curr.implied_mid_price) - mid) / mid
                if diff >= 0.02:
                    implied_inconsistency += 1

        steps = max(1, len(samples) - 1)
        flicker_frequency = flickers / steps
        depth_persistence = persistence_hits / steps
        disappearing_top_rate = disappearing_top_hits / steps
        wall_nonfill_rate = wall_nonfill_hits / steps
        inversion_rate = inversions / steps
        implied_inconsistency_rate = implied_inconsistency / steps

        avg_depth = sum(total_depths) / max(1, len(total_depths))
        spread_instability = 0.0
        if len(spreads) > 1:
            avg_spread = sum(spreads) / len(spreads)
            spread_instability = (
                sum(abs(s - avg_spread) for s in spreads) / len(spreads)
            ) / max(1e-6, avg_spread)
        spread_instability = max(0.0, min(1.0, spread_instability))

        depth_reliability_score = max(
            0.0,
            min(
                1.0,
                (depth_persistence * 0.55)
                + ((1.0 - flicker_frequency) * 0.25)
                + (min(1.0, avg_depth / 1500.0) * 0.20),
            ),
        )

        path_distortion_risk = max(
            0.0,
            min(
                1.0,
                (spread_instability * 0.45)
                + (inversion_rate * 0.30)
                + (implied_inconsistency_rate * 0.25),
            ),
        )

        fundedness_uncertainty = max(
            0.0,
            min(
                1.0,
                (disappearing_top_rate * 0.50)
                + (wall_nonfill_rate * 0.30)
                + ((1.0 - depth_reliability_score) * 0.20),
            ),
        )

        observation_confidence = max(
            0.01,
            min(
                1.0,
                1.0
                - (
                    ((1.0 - depth_reliability_score) * 0.45)
                    + (path_distortion_risk * 0.30)
                    + (fundedness_uncertainty * 0.25)
                ),
            ),
        )

        return ObservationUncertaintyResult(
            depth_reliability_score=depth_reliability_score,
            path_distortion_risk=path_distortion_risk,
            fundedness_uncertainty=fundedness_uncertainty,
            observation_confidence=observation_confidence,
        )
