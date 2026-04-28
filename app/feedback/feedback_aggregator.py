from __future__ import annotations

import json
from dataclasses import dataclass

from app.db.models import ExecutionRecord
from app.feedback.decision_outcome import (
    DecisionOutcomeEvaluation,
    DecisionOutcomeModel,
    build_decision_outcome_from_shadow_execution,
)


def _is_shadow_execution(row: ExecutionRecord) -> bool:
    try:
        details = json.loads(str(row.execution_details_json or "{}"))
    except json.JSONDecodeError:
        return False
    return bool(details.get("shadow"))


@dataclass(slots=True)
class DecisionFeedbackSample:
    decision_id: int
    predicted_fill_probability: float
    realised_fill_ratio: float
    predicted_ev: float
    realised_ev_proxy: float
    fill_error: float
    ev_error: float
    ledger_penalty: float
    route_instability: float
    competition_proxy: float
    weighted_error: float
    allow_trade: bool


@dataclass(slots=True)
class DecisionFeedbackAggregate:
    avg_fill_error: float
    avg_ev_error: float
    overconfidence_rate: float
    underconfidence_rate: float
    avg_ledger_penalty: float
    avg_route_instability: float
    competition_proxy_rate: float
    sample_count: int
    samples: list[DecisionFeedbackSample]


class DecisionFeedbackAggregator:
    def aggregate_from_executions(self, executions: list[ExecutionRecord]) -> DecisionFeedbackAggregate:
        outcomes = [build_decision_outcome_from_shadow_execution(row) for row in executions if _is_shadow_execution(row)]
        return self.aggregate(outcomes)

    def aggregate(self, outcomes) -> DecisionFeedbackAggregate:
        model = DecisionOutcomeModel()
        samples: list[DecisionFeedbackSample] = []
        overconfidence = 0
        underconfidence = 0
        for outcome in outcomes:
            analysis: DecisionOutcomeEvaluation = model.evaluate(outcome)
            if analysis.overconfidence:
                overconfidence += 1
            if analysis.underconfidence:
                underconfidence += 1
            samples.append(
                DecisionFeedbackSample(
                    decision_id=outcome.decision_id,
                    predicted_fill_probability=outcome.predicted_fill_probability,
                    realised_fill_ratio=analysis.realised_fill_ratio,
                    predicted_ev=outcome.predicted_ev,
                    realised_ev_proxy=analysis.realised_ev_proxy,
                    fill_error=analysis.fill_error,
                    ev_error=analysis.ev_error,
                    ledger_penalty=analysis.ledger_penalty,
                    route_instability=analysis.route_penalty,
                    competition_proxy=analysis.competition_proxy,
                    weighted_error=analysis.weighted_error,
                    allow_trade=outcome.allow_trade,
                )
            )

        if not samples:
            return DecisionFeedbackAggregate(
                avg_fill_error=0.0,
                avg_ev_error=0.0,
                overconfidence_rate=0.0,
                underconfidence_rate=0.0,
                avg_ledger_penalty=0.0,
                avg_route_instability=0.0,
                competition_proxy_rate=0.0,
                sample_count=0,
                samples=[],
            )

        count = len(samples)
        return DecisionFeedbackAggregate(
            avg_fill_error=round(sum(row.fill_error for row in samples) / count, 6),
            avg_ev_error=round(sum(row.ev_error for row in samples) / count, 6),
            overconfidence_rate=round(overconfidence / count, 6),
            underconfidence_rate=round(underconfidence / count, 6),
            avg_ledger_penalty=round(sum(row.ledger_penalty for row in samples) / count, 6),
            avg_route_instability=round(sum(row.route_instability for row in samples) / count, 6),
            competition_proxy_rate=round(sum(row.competition_proxy for row in samples) / count, 6),
            sample_count=count,
            samples=samples,
        )