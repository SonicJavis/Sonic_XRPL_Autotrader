from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone

from app.db.models import ExecutionRecord


def _clamp_unit(raw: float) -> float:
    return max(0.0, min(1.0, float(raw)))


def _utc(ts: datetime) -> datetime:
    if ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def _execution_details(row: ExecutionRecord) -> dict[str, object]:
    try:
        return json.loads(str(row.execution_details_json or "{}"))
    except json.JSONDecodeError:
        return {}


@dataclass(slots=True)
class DecisionOutcome:
    decision_id: int
    timestamp: datetime
    requested_size: float
    expected_profit: float
    expected_loss: float
    predicted_fill_probability: float
    predicted_ev: float
    allow_trade: bool
    observed_fill_ratio: float
    observed_possible_fill: float
    route_used: str | None
    ledger_gap: int
    route_confidence: float
    simulated_fill_ratio: float


@dataclass(slots=True)
class DecisionOutcomeEvaluation:
    realised_fill_ratio: float
    realised_ev_proxy: float
    ledger_penalty: float
    route_penalty: float
    competition_proxy: float
    fill_error: float
    ev_error: float
    confidence_error: float
    weighted_error: float
    overconfidence: bool
    underconfidence: bool


class DecisionOutcomeModel:
    def evaluate(self, outcome: DecisionOutcome) -> DecisionOutcomeEvaluation:
        predicted_fill_probability = _clamp_unit(outcome.predicted_fill_probability)
        realised_fill_ratio = _clamp_unit(outcome.observed_fill_ratio)
        ledger_gap = max(0, int(outcome.ledger_gap))
        ledger_penalty = _clamp_unit(ledger_gap / 3.0)
        route_penalty = _clamp_unit(1.0 - _clamp_unit(outcome.route_confidence))
        competition_proxy = 1.0 if float(outcome.simulated_fill_ratio) > (realised_fill_ratio + 0.30) else 0.0
        realised_ev_proxy = (realised_fill_ratio * float(outcome.expected_profit)) - (
            (1.0 - realised_fill_ratio) * float(outcome.expected_loss)
        )
        fill_error = predicted_fill_probability - realised_fill_ratio
        ev_error = float(outcome.predicted_ev) - realised_ev_proxy
        confidence_error = abs(fill_error) * (1.0 + ledger_penalty + route_penalty)
        weighted_error = confidence_error + abs(ev_error)
        return DecisionOutcomeEvaluation(
            realised_fill_ratio=round(realised_fill_ratio, 6),
            realised_ev_proxy=round(realised_ev_proxy, 6),
            ledger_penalty=round(ledger_penalty, 6),
            route_penalty=round(route_penalty, 6),
            competition_proxy=round(competition_proxy, 6),
            fill_error=round(fill_error, 6),
            ev_error=round(ev_error, 6),
            confidence_error=round(confidence_error, 6),
            weighted_error=round(weighted_error, 6),
            overconfidence=fill_error > 0.10,
            underconfidence=fill_error < -0.10,
        )


def build_decision_outcome_from_shadow_execution(execution: ExecutionRecord) -> DecisionOutcome:
    details = _execution_details(execution)
    requested_size = max(0.0, float(execution.requested_size or 0.0))
    simulated_fill_ratio = 0.0 if requested_size <= 0 else _clamp_unit(float(execution.filled_size or 0.0) / requested_size)
    expected_profit = float(details.get("expected_profit", max(1.0, requested_size * 0.05)))
    expected_loss = max(0.0, float(details.get("expected_loss", max(1.0, requested_size * 0.03))))
    predicted_fill_probability = _clamp_unit(float(details.get("predicted_fill_probability", simulated_fill_ratio)))
    predicted_ev = float(
        details.get(
            "predicted_ev",
            (predicted_fill_probability * expected_profit) - ((1.0 - predicted_fill_probability) * expected_loss),
        )
    )
    observed_fill_ratio = _clamp_unit(float(details.get("observed_fill_ratio", simulated_fill_ratio)))
    observed_possible_fill = min(requested_size, max(0.0, float(details.get("observed_possible_fill", observed_fill_ratio * requested_size))))
    routes_seen = details.get("routes_seen", [])
    route_used: str | None = None
    if isinstance(details.get("route_used"), str):
        route_used = str(details.get("route_used"))
    elif isinstance(routes_seen, list) and routes_seen:
        route_used = str(routes_seen[0])
    path_execution_risk = _clamp_unit(float(details.get("path_execution_risk", 0.0)))
    route_confidence = _clamp_unit(float(details.get("route_confidence", max(0.0, 1.0 - path_execution_risk))))
    ledger_gap = max(0, int(execution.ledger_index_execution or 0) - int(execution.ledger_index_snapshot or 0))
    allow_trade = bool(details.get("allow_trade", predicted_ev > 0.0 and predicted_fill_probability > 0.35))
    return DecisionOutcome(
        decision_id=int(execution.id or 0),
        timestamp=_utc(execution.execution_time),
        requested_size=requested_size,
        expected_profit=expected_profit,
        expected_loss=expected_loss,
        predicted_fill_probability=round(predicted_fill_probability, 6),
        predicted_ev=round(predicted_ev, 6),
        allow_trade=allow_trade,
        observed_fill_ratio=round(observed_fill_ratio, 6),
        observed_possible_fill=round(observed_possible_fill, 6),
        route_used=route_used,
        ledger_gap=ledger_gap,
        route_confidence=round(route_confidence, 6),
        simulated_fill_ratio=round(simulated_fill_ratio, 6),
    )