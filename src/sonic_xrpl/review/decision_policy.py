from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sonic_xrpl.signals.models import CandidateRiskSignal
from sonic_xrpl.signals.evidence import stable_id
from sonic_xrpl.review.models import SignalReviewItem, PaperDecision, PaperTradeIntent, ReviewQueue


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def classify_candidate_for_phase50(candidate: CandidateRiskSignal, market_snapshot=None) -> tuple[SignalReviewItem, PaperDecision, PaperTradeIntent]:
    # Deterministic ids
    review_id = stable_id("rev", candidate.candidate_id, candidate.signal_type.value, str(candidate.confidence_score), str(candidate.risk_score), \
                          ",".join(candidate.missing_required_evidence))
    paper_decision_id = stable_id("pd", candidate.candidate_id, candidate.signal_type.value, str(candidate.confidence_score))
    intent_id = stable_id("pi", candidate.candidate_id, candidate.signal_id)

    signal_id = getattr(candidate, "signal_id", "SIG-UNKNOWN")
    # Classification mapping (Phase 50 follows Phase 49 semantics)
    classification = candidate.signal_type.value

    # Decision recommendation mapping for paper review
    if classification == "BUY_CANDIDATE":
        decision_recommendation = "PAPER_REVIEW"
        decision = "PAPER_APPROVE"  # paper-only final step would be an approval
    elif classification == "WATCH":
        decision_recommendation = "PAPER_WATCH"
        decision = "PAPER_WATCH"
    elif classification == "AVOID":
        decision_recommendation = "PAPER_REJECT"
        decision = "PAPER_REJECT"
    else:
        decision_recommendation = "INSUFFICIENT_EVIDENCE"
        decision = "NEEDS_MORE_EVIDENCE"

    missing_evidence = tuple(candidate.missing_required_evidence)
    limitations = tuple(candidate.limitations) if hasattr(candidate, "limitations") else tuple()
    evidence_summary = ", ".join(list(candidate.reasons) ) if hasattr(candidate, 'reasons') else ("EVIDENCE_SUMMARY_NOT_AVAILABLE")
    created_at = _now_iso()

    review_item = SignalReviewItem(
        review_id=review_id,
        candidate_id=candidate.candidate_id,
        signal_id=signal_id,
        issuer="",
        currency="",
        classification=classification,
        confidence_score=candidate.confidence_score,
        risk_score=candidate.risk_score,
        decision_recommendation=decision_recommendation,
        evidence_summary=evidence_summary,
        missing_evidence=missing_evidence,
        limitations=limitations if isinstance(limitations, tuple) else tuple(),
        provenance=("Phase50_offline_review",),
        synthetic=getattr(candidate, 'synthetic', False),
        created_at=created_at,
        live_execution_allowed=False,
    )

    paper_decision = PaperDecision(
        decision_id=paper_decision_id,
        review_id=review_id,
        candidate_id=candidate.candidate_id,
        signal_id=signal_id,
        decision=decision,
        reason_codes=(classification, ),
        human_review_required=True,
        live_execution_allowed=False,
        paper_only=True,
        generated_at=created_at,
        limitations=tuple(),
    )

    paper_intent = PaperTradeIntent(
        intent_id=intent_id,
        decision_id=paper_decision_id,
        candidate_id=candidate.candidate_id,
        issuer="",
        currency="",
        side="BUY_SIMULATED" if decision == "PAPER_APPROVE" else ("WATCH_ONLY" if decision == "PAPER_WATCH" else "REJECTED"),
        sizing_mode="FIXED_TEST_SIZE",
        notional_xrp=1 if decision == "PAPER_APPROVE" else None,
        max_slippage_bps=None,
        created_from_signal_id=getattr(candidate, 'signal_id', signal_id),
        live_execution_allowed=False,
        requires_human_review=True,
        execution_block_reason="Live execution blocked by Phase 50: paper-only review",
    )

    return review_item, paper_decision, paper_intent
