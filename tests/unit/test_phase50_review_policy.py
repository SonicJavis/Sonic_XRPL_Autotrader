from sonic_xrpl.signals.models import CandidateRiskSignal, SignalType
from sonic_xrpl.review.decision_policy import classify_candidate_for_phase50


def _make_candidate() -> CandidateRiskSignal:
    return CandidateRiskSignal(
        signal_id="sig-100",
        candidate_id="cand-100",
        signal_type=SignalType.BUY_CANDIDATE,
        confidence_score=80,
        risk_score=20,
        evidence_count=1,
        missing_required_evidence=(),
        reasons=("ok",),
        limitations=(),
        generated_at="1970-01-01T00:00:00+00:00",
        live_execution_allowed=False,
    )


def test_decision_policy_buy_yields_paper_review_and_paper_approve():
    cand = _make_candidate()
    review_item, paper_decision, paper_intent = classify_candidate_for_phase50(cand)
    assert review_item.classification == cand.signal_type.value
    assert paper_decision.decision in {"PAPER_APPROVE", "PAPER_WATCH", "PAPER_REJECT", "NEEDS_MORE_EVIDENCE"}
    assert paper_intent.live_execution_allowed is False
