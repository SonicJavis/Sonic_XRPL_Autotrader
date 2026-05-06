"""FirstLedger candidate signal pipeline."""

from __future__ import annotations

from pathlib import Path

from sonic_xrpl.market.models import MarketSnapshot
from sonic_xrpl.signals.classifier import classify_candidates
from sonic_xrpl.signals.evidence import evidence_from_rows, load_candidate_rows
from sonic_xrpl.signals.models import CandidateRiskSignal, FirstLedgerCandidateEvidence

EMPTY_STATE = "No source-backed FirstLedger launches available."


def load_firstledger_candidate_evidence(fixture: str | Path) -> list[FirstLedgerCandidateEvidence]:
    """Load source-backed or clearly labelled synthetic fixture evidence offline."""
    return evidence_from_rows(load_candidate_rows(fixture))


def generate_firstledger_signals(
    fixture: str | Path,
    market_snapshot: MarketSnapshot | None = None,
) -> list[CandidateRiskSignal]:
    """Generate deterministic non-executing FirstLedger signals."""
    return classify_candidates(load_firstledger_candidate_evidence(fixture), market_snapshot)
