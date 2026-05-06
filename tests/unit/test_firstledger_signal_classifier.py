from sonic_xrpl.market.models import AssetSnapshot, AssetType, MarketSnapshot, SnapshotQuality, SnapshotRecommendation
from sonic_xrpl.signals.classifier import classify_candidate
from sonic_xrpl.signals.evidence import evidence_from_rows, load_candidate_rows
from sonic_xrpl.signals.models import SignalType


def _snapshot_for(issuer: str, currency: str) -> MarketSnapshot:
    return MarketSnapshot(
        snapshot_id="snap_phase49",
        created_at="2026-05-05T11:00:00+00:00",
        fixture_id="phase49",
        ledger_index=900001,
        network="fixture",
        assets=[AssetSnapshot(f"{currency}.{issuer}", AssetType.IOU, issuer, currency, None, ["TrustSet"], [], [])],
        amms=[], orderbooks=[], accounts=[], trustlines=[], mpt_holders=[], metadata_signals=[],
        capabilities={},
        quality=SnapshotQuality(80, {}, [], [], [], [], SnapshotRecommendation.USABLE_FOR_RESEARCH),
        limitations=[],
        source_hash="fixture",
    )


def _candidate(path):
    return evidence_from_rows(load_candidate_rows(path))[0]


def test_buy_candidate_requires_minimum_evidence_and_snapshot():
    candidate = _candidate("tests/fixtures/firstledger/source_backed_candidates.json")
    signal = classify_candidate(candidate, _snapshot_for(candidate.issuer, candidate.currency))
    assert signal.signal_type == SignalType.BUY_CANDIDATE
    assert signal.live_execution_allowed is False
    assert signal.missing_required_evidence == ()


def test_watch_for_partial_evidence_without_snapshot():
    signal = classify_candidate(_candidate("tests/fixtures/firstledger/source_backed_candidates.json"))
    assert signal.signal_type == SignalType.WATCH
    assert "market_snapshot_context_missing" in signal.limitations


def test_avoid_for_explicit_risk_evidence():
    signal = classify_candidate(_candidate("tests/fixtures/firstledger/avoid_candidate_explicit_risk.json"))
    assert signal.signal_type == SignalType.AVOID


def test_insufficient_evidence_for_missing_required_fields_and_synthetic():
    missing = classify_candidate(_candidate("tests/fixtures/firstledger/missing_required_fields.json"))
    synthetic = classify_candidate(_candidate("tests/fixtures/firstledger/synthetic_candidates.json"))
    assert missing.signal_type == SignalType.INSUFFICIENT_EVIDENCE
    assert "currency" in missing.missing_required_evidence
    assert "issuer" in missing.missing_required_evidence
    assert synthetic.signal_type == SignalType.INSUFFICIENT_EVIDENCE


def test_deterministic_signal_id():
    candidate = _candidate("tests/fixtures/firstledger/source_backed_candidates.json")
    assert classify_candidate(candidate).signal_id == classify_candidate(candidate).signal_id
