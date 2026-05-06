from sonic_xrpl.signals.models import CandidateRiskSignal, SignalType


def test_candidate_risk_signal_live_execution_always_false_by_contract():
    signal = CandidateRiskSignal(
        signal_id="sig_test",
        candidate_id="candidate",
        signal_type=SignalType.WATCH,
        confidence_score=10,
        risk_score=90,
        evidence_count=1,
        missing_required_evidence=("issuer",),
        reasons=("test",),
        limitations=("test",),
        generated_at="1970-01-01T00:00:00+00:00",
    )
    assert signal.live_execution_allowed is False
