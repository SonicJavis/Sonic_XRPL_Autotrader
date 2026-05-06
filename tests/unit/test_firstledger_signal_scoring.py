from sonic_xrpl.market.models import AssetSnapshot, AssetType, MarketSnapshot, SnapshotManifest, SnapshotQuality, SnapshotRecommendation
from sonic_xrpl.signals.evidence import evidence_from_rows, load_candidate_rows
from sonic_xrpl.signals.scoring import score_candidate


def _snapshot_for(issuer: str, currency: str) -> MarketSnapshot:
    return MarketSnapshot(
        snapshot_id="snap_phase49",
        created_at="2026-05-05T11:00:00+00:00",
        fixture_id="phase49",
        ledger_index=900001,
        network="fixture",
        assets=[AssetSnapshot(f"{currency}.{issuer}", AssetType.IOU, issuer, currency, None, ["TrustSet"], [], [])],
        amms=[],
        orderbooks=[],
        accounts=[],
        trustlines=[],
        mpt_holders=[],
        metadata_signals=[],
        capabilities={},
        quality=SnapshotQuality(80, {}, [], [], [], [], SnapshotRecommendation.USABLE_FOR_RESEARCH),
        limitations=[],
        source_hash="fixture",
    )


def test_scoring_is_deterministic_and_penalizes_missing_snapshot():
    candidate = evidence_from_rows(load_candidate_rows("tests/fixtures/firstledger/source_backed_candidates.json"))[0]
    no_snapshot = score_candidate(candidate)
    with_snapshot = score_candidate(candidate, _snapshot_for(candidate.issuer, candidate.currency))
    assert no_snapshot == score_candidate(candidate)
    assert with_snapshot.final_score > no_snapshot.final_score
    assert no_snapshot.market_snapshot_score == 0


def test_missing_required_fields_reduce_score():
    candidate = evidence_from_rows(load_candidate_rows("tests/fixtures/firstledger/missing_required_fields.json"))[0]
    score = score_candidate(candidate)
    assert score.unknown_penalty >= 24
    assert score.final_score < 50
