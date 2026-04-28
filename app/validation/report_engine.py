from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ValidationSample:
    token_key: str
    disagreement_score: float
    false_confidence_flag: bool
    observation_confidence: float
    simulator_within_bounds: bool


@dataclass(slots=True)
class UncertaintyReport:
    disagreement_score: float
    false_confidence_rate: float
    observation_confidence_avg: float
    simulator_within_bounds_rate: float
    worst_tokens: list[dict[str, float | str]]
    recommendation: str


class UncertaintyReportEngine:
    def build(self, samples: list[ValidationSample]) -> UncertaintyReport:
        if not samples:
            return UncertaintyReport(
                disagreement_score=1.0,
                false_confidence_rate=0.0,
                observation_confidence_avg=0.0,
                simulator_within_bounds_rate=0.0,
                worst_tokens=[],
                recommendation="COLLECT_MORE_DATA",
            )

        total = len(samples)
        avg_disagreement = sum(max(0.0, min(1.0, s.disagreement_score)) for s in samples) / total
        false_confidence_rate = sum(1 for s in samples if s.false_confidence_flag) / total
        observation_confidence_avg = sum(max(0.0, min(1.0, s.observation_confidence)) for s in samples) / total
        simulator_within_bounds_rate = sum(1 for s in samples if s.simulator_within_bounds) / total

        token_totals: dict[str, list[float]] = {}
        for s in samples:
            token_totals.setdefault(s.token_key, []).append(max(0.0, min(1.0, s.disagreement_score)))
        worst_tokens = [
            {"token": token, "avg_disagreement": sum(vals) / len(vals)}
            for token, vals in token_totals.items()
        ]
        worst_tokens.sort(key=lambda it: float(it["avg_disagreement"]), reverse=True)
        worst_tokens = worst_tokens[:5]

        recommendation = "HOLD"
        if avg_disagreement >= 0.50:
            recommendation = "HARDEN_ASSUMPTIONS"
        elif observation_confidence_avg <= 0.40:
            recommendation = "COLLECT_MORE_DATA"
        elif avg_disagreement <= 0.25 and observation_confidence_avg >= 0.55:
            recommendation = "HOLD"

        return UncertaintyReport(
            disagreement_score=round(avg_disagreement, 6),
            false_confidence_rate=round(false_confidence_rate, 6),
            observation_confidence_avg=round(observation_confidence_avg, 6),
            simulator_within_bounds_rate=round(simulator_within_bounds_rate, 6),
            worst_tokens=worst_tokens,
            recommendation=recommendation,
        )
