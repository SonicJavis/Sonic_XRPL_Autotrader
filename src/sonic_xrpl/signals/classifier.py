"""FirstLedger candidate risk signal classifier."""

from __future__ import annotations

from datetime import datetime, timezone

from sonic_xrpl.market.models import MarketSnapshot
from sonic_xrpl.signals.evidence import REQUIRED_FIELDS, atomic_signal_evidence, stable_id
from sonic_xrpl.signals.models import CandidateRiskSignal, FirstLedgerCandidateEvidence, SignalType
from sonic_xrpl.signals.scoring import has_critical_limitation, score_candidate

_GENERATED_AT = "1970-01-01T00:00:00+00:00"


def missing_required_evidence(candidate: FirstLedgerCandidateEvidence) -> tuple[str, ...]:
    """Return missing required fields without hiding unknown values."""
    missing = set(candidate.raw_fields_missing)
    if candidate.observed_at == "" and "observed_at_missing" in candidate.limitations:
        missing.discard("observed_at")
    return tuple(sorted(missing))


def classify_candidate(
    candidate: FirstLedgerCandidateEvidence,
    market_snapshot: MarketSnapshot | None = None,
    *,
    generated_at: str = _GENERATED_AT,
) -> CandidateRiskSignal:
    """Classify one candidate into a deterministic advisory signal."""
    scoring = score_candidate(candidate, market_snapshot)
    missing = missing_required_evidence(candidate)
    atoms = atomic_signal_evidence(candidate)
    limitations = list(candidate.limitations)
    reasons: list[str] = []

    if market_snapshot is None:
        limitations.append("market_snapshot_context_missing")
    if candidate.observed_at == "":
        limitations.append("observed_at_source_missing_no_synthetic_timestamp")

    if has_critical_limitation(candidate):
        signal_type = SignalType.AVOID
        reasons.append("Explicit avoid-level risk evidence is present.")
    elif missing:
        signal_type = SignalType.INSUFFICIENT_EVIDENCE
        reasons.append("Missing required evidence blocks BUY_CANDIDATE: " + ", ".join(missing))
    elif candidate.synthetic:
        signal_type = SignalType.INSUFFICIENT_EVIDENCE
        reasons.append("Synthetic fixtures cannot produce BUY_CANDIDATE.")
    elif candidate.metadata_status != "validated":
        signal_type = SignalType.WATCH
        reasons.append("Metadata is not validated, so the candidate remains watch-only.")
    elif market_snapshot is None:
        signal_type = SignalType.WATCH
        reasons.append("Market snapshot context is unavailable and documented as a limitation.")
    elif scoring.final_score >= 50:
        signal_type = SignalType.BUY_CANDIDATE
        reasons.append("Minimum offline evidence requirements passed; this is not execution approval.")
    else:
        signal_type = SignalType.WATCH
        reasons.append("Evidence is partial or conservative score is below BUY_CANDIDATE threshold.")

    reasons.append(f"Conservative final evidence score: {scoring.final_score}/100.")
    reasons.append("live_execution_allowed is always False for Phase 49 signals.")
    signal_id = stable_id("sig", candidate.candidate_id, signal_type.value, scoring.final_score, tuple(sorted(set(limitations))))
    risk_score = max(0, min(100, 100 - scoring.final_score))
    return CandidateRiskSignal(
        signal_id=signal_id,
        candidate_id=candidate.candidate_id,
        signal_type=signal_type,
        confidence_score=scoring.final_score,
        risk_score=risk_score,
        evidence_count=sum(1 for atom in atoms if atom.source_backed),
        missing_required_evidence=missing,
        reasons=tuple(reasons),
        limitations=tuple(dict.fromkeys(limitations)),
        generated_at=generated_at,
        live_execution_allowed=False,
    )


def classify_candidates(
    candidates: list[FirstLedgerCandidateEvidence],
    market_snapshot: MarketSnapshot | None = None,
    *,
    generated_at: str = _GENERATED_AT,
) -> list[CandidateRiskSignal]:
    """Classify candidates in deterministic order."""
    return [classify_candidate(candidate, market_snapshot, generated_at=generated_at) for candidate in sorted(candidates, key=lambda c: c.candidate_id)]
