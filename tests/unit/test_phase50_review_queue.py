from sonic_xrpl.review.models import ReviewQueue, SignalReviewItem, PaperDecision, PaperTradeIntent
from sonic_xrpl.signals.models import CandidateRiskSignal, SignalType
from sonic_xrpl.review.decision_policy import classify_candidate_for_phase50

def test_review_queue_basic_structure():
    cand = CandidateRiskSignal(
        signal_id="sig-200",
        candidate_id="cand-200",
        signal_type=SignalType.BUY_CANDIDATE,
        confidence_score=70,
        risk_score=30,
        evidence_count=1,
        missing_required_evidence=(),
        reasons=("r1",),
        limitations=(),
        generated_at="1970-01-01T00:00:00+00:00",
        live_execution_allowed=False,
    )
    review_item, paper_decision, paper_intent = classify_candidate_for_phase50(cand)
    queue = ReviewQueue(queue_id="q1", items=(review_item,), generated_at="1970-01-01T00:00:00+00:00", source_fixture="fixture")
    assert queue.queue_id == "q1"
    assert len(queue.items) == 1
    assert isinstance(queue.items[0], SignalReviewItem)
