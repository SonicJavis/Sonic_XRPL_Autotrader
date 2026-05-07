from sonic_xrpl.outcomes.attribution import build_outcome_attributions
from sonic_xrpl.outcomes.feedback import build_signal_feedback
from sonic_xrpl.outcomes.models import OutcomeLabel
from sonic_xrpl.outcomes.observation import load_outcome_observations
from sonic_xrpl.signals.firstledger_candidate import generate_firstledger_signals


def test_phase51_attributes_fixture_observation_to_signal():
    signals = generate_firstledger_signals("tests/fixtures/firstledger/source_backed_candidates.json")
    observations = load_outcome_observations("tests/fixtures/outcomes/paper_observations.json")

    attributions = build_outcome_attributions(signals, observations)

    assert len(attributions) == 1
    attribution = attributions[0]
    assert attribution.candidate_id == "fixture_source_backed_watch"
    assert attribution.signal_type == "WATCH"
    assert attribution.outcome_label == OutcomeLabel.WIN
    assert attribution.observed_return_bps == 1200.0
    assert attribution.baseline_return_bps == 500.0
    assert attribution.excess_return_bps == 700.0
    assert attribution.paper_only is True
    assert attribution.live_execution_allowed is False


def test_phase51_missing_observation_is_explicit():
    signals = generate_firstledger_signals("tests/fixtures/firstledger/source_backed_candidates.json")

    attributions = build_outcome_attributions(signals, [])

    attribution = attributions[0]
    assert attribution.outcome_label == OutcomeLabel.NO_OBSERVATION
    assert attribution.observed_return_bps is None
    assert "paper_outcome_observation_missing" in attribution.limitations
    assert attribution.live_execution_allowed is False


def test_phase51_feedback_aggregates_by_signal_type():
    signals = generate_firstledger_signals("tests/fixtures/firstledger/source_backed_candidates.json")
    observations = load_outcome_observations("tests/fixtures/outcomes/paper_observations.json")
    attributions = build_outcome_attributions(signals, observations)

    feedback = build_signal_feedback(attributions)

    assert feedback.total_attributed == 1
    assert feedback.wins == 1
    assert feedback.losses == 0
    assert feedback.by_signal_type["WATCH"].count == 1
    assert feedback.by_signal_type["WATCH"].average_observed_return_bps == 1200.0
    assert feedback.paper_only is True
    assert feedback.live_execution_allowed is False
