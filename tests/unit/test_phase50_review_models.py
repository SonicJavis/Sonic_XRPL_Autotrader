import datetime
from sonic_xrpl.signals.models import CandidateRiskSignal, SignalType
from sonic_xrpl.review.decision_policy import classify_candidate_for_phase50


def _dummy_candidate():
    return CandidateRiskSignal(
        signal_id="sig-1",
        candidate_id="cand-1",
        signal_type=SignalType.BUY_CANDIDATE,
        confidence_score=75,
        risk_score=25,
        evidence_count=1,
        missing_required_evidence=(),
        reasons=("example_reason",),
        limitations=("none",),
        generated_at="1970-01-01T00:00:00+00:00",
        live_execution_allowed=False,
    )


def test_phase50_review_item_and_paper_decision_generation():
    cand = _dummy_candidate()
    review_item, paper_decision, paper_intent = classify_candidate_for_phase50(cand)
    # Basic structure checks
    assert review_item.candidate_id == cand.candidate_id
    assert review_item.signal_id == cand.signal_id
    assert review_item.live_execution_allowed is False
    assert review_item.classification == cand.signal_type.value
    assert paper_decision.candidate_id == cand.candidate_id
    assert paper_intent.decision_id == paper_decision.decision_id
    assert paper_intent.live_execution_allowed is False
