from __future__ import annotations

from fastapi import APIRouter, Request
from sqlmodel import select

from app.db.models import ExecutionRecord
from app.feedback.feedback_aggregator import DecisionFeedbackAggregator

router = APIRouter()


@router.get("/feedback/decision-quality")
def feedback_decision_quality(request: Request, limit: int = 500) -> dict[str, object]:
    container = request.app.state.container
    safe_limit = min(max(limit, 1), 5000)
    with container.session_factory() as session:
        executions = session.exec(
            select(ExecutionRecord).order_by(ExecutionRecord.id.desc()).limit(safe_limit)
        ).all()
    aggregate = DecisionFeedbackAggregator().aggregate_from_executions(executions)
    return {
        "avg_fill_error": aggregate.avg_fill_error,
        "avg_ev_error": aggregate.avg_ev_error,
        "overconfidence_rate": aggregate.overconfidence_rate,
        "underconfidence_rate": aggregate.underconfidence_rate,
        "avg_ledger_penalty": aggregate.avg_ledger_penalty,
        "avg_route_instability": aggregate.avg_route_instability,
        "competition_proxy_rate": aggregate.competition_proxy_rate,
        "sample_count": aggregate.sample_count,
        "is_advisory": True,
        "is_shadow": True,
        "is_executable": False,
        "xrpl_warning": "XRPL outcomes are probabilistic and ledger-dependent",
    }