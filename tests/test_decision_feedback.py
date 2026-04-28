from datetime import datetime, timezone

from app.feedback.decision_outcome import DecisionOutcome, DecisionOutcomeModel
from app.feedback.feedback_aggregator import DecisionFeedbackAggregator


def _outcome(
    *,
    decision_id: int = 1,
    predicted_fill_probability: float = 0.8,
    predicted_ev: float = 10.0,
    observed_fill_ratio: float = 0.4,
    expected_profit: float = 20.0,
    expected_loss: float = 10.0,
    route_confidence: float = 0.6,
    ledger_gap: int = 1,
    simulated_fill_ratio: float = 0.8,
    allow_trade: bool = True,
) -> DecisionOutcome:
    return DecisionOutcome(
        decision_id=decision_id,
        timestamp=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
        requested_size=100.0,
        expected_profit=expected_profit,
        expected_loss=expected_loss,
        predicted_fill_probability=predicted_fill_probability,
        predicted_ev=predicted_ev,
        allow_trade=allow_trade,
        observed_fill_ratio=observed_fill_ratio,
        observed_possible_fill=observed_fill_ratio * 100.0,
        route_used="direct",
        ledger_gap=ledger_gap,
        route_confidence=route_confidence,
        simulated_fill_ratio=simulated_fill_ratio,
    )


def test_ledger_penalty_scales_with_gap() -> None:
    model = DecisionOutcomeModel()
    low = model.evaluate(_outcome(ledger_gap=1))
    high = model.evaluate(_outcome(ledger_gap=3))
    assert low.ledger_penalty == 0.333333
    assert high.ledger_penalty == 1.0


def test_route_penalty_falls_back_from_route_confidence() -> None:
    model = DecisionOutcomeModel()
    result = model.evaluate(_outcome(route_confidence=0.25))
    assert result.route_penalty == 0.75


def test_weighted_error_increases_with_instability() -> None:
    model = DecisionOutcomeModel()
    stable = model.evaluate(_outcome(route_confidence=0.9, ledger_gap=0))
    unstable = model.evaluate(_outcome(route_confidence=0.2, ledger_gap=3))
    assert unstable.weighted_error > stable.weighted_error


def test_deterministic_aggregation() -> None:
    aggregator = DecisionFeedbackAggregator()
    outcomes = [_outcome(decision_id=1), _outcome(decision_id=2, predicted_fill_probability=0.6, observed_fill_ratio=0.5)]
    first = aggregator.aggregate(outcomes)
    second = aggregator.aggregate(outcomes)
    assert first == second


def test_overconfidence_detection() -> None:
    aggregator = DecisionFeedbackAggregator()
    result = aggregator.aggregate(
        [
            _outcome(decision_id=1, predicted_fill_probability=0.9, observed_fill_ratio=0.2),
            _outcome(decision_id=2, predicted_fill_probability=0.2, observed_fill_ratio=0.8),
        ]
    )
    assert result.overconfidence_rate == 0.5
    assert result.underconfidence_rate == 0.5
