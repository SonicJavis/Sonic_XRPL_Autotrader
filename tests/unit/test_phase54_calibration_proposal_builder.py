from pathlib import Path

from sonic_xrpl.calibration_proposal import build_calibration_proposal_pack


FIXTURE_DIR = Path("tests/fixtures/calibration_proposal")


def test_ready_fixture_produces_exact_conservative_proposals():
    pack = build_calibration_proposal_pack(FIXTURE_DIR / "ready_for_review_recommendations.json")

    assert len(pack.proposals) == 2
    assert len(pack.blocked_recommendations) == 1
    values = {item.parameter_ref.name: item for item in pack.proposals}
    assert values["watch_threshold"].current_value == 0.5
    assert values["watch_threshold"].proposed_value == 0.48
    assert values["signal_score_threshold"].current_value == 0.7
    assert values["signal_score_threshold"].proposed_value == 0.72
    assert all(item.auto_apply_allowed is False for item in pack.proposals)
    assert all(item.human_review_required is True for item in pack.proposals)


def test_insufficient_evidence_produces_blocked_proposals():
    pack = build_calibration_proposal_pack(FIXTURE_DIR / "insufficient_evidence_recommendations.json")

    assert pack.proposals == ()
    assert pack.blocked_recommendations
    assert "does not request an exact" in pack.blocked_recommendations[0].reason


def test_invalid_observations_block_exact_proposals():
    pack = build_calibration_proposal_pack(FIXTURE_DIR / "invalid_observation_recommendations.json")

    assert pack.proposals == ()
    assert "Invalid numeric observations" in pack.blocked_recommendations[0].reason


def test_synthetic_heavy_evidence_blocks_exact_proposals():
    pack = build_calibration_proposal_pack(FIXTURE_DIR / "synthetic_heavy_recommendations.json")

    assert pack.proposals == ()
    assert pack.risk_summary.synthetic_ratio > 0
    assert "Synthetic evidence" in pack.blocked_recommendations[0].reason


def test_sparse_signal_classes_block_confident_exact_proposals():
    pack = build_calibration_proposal_pack(FIXTURE_DIR / "sparse_class_recommendations.json")

    assert pack.proposals == ()
    assert "Sparse signal classes" in pack.blocked_recommendations[0].reason


def test_pack_and_proposal_ids_are_deterministic():
    first = build_calibration_proposal_pack(FIXTURE_DIR / "ready_for_review_recommendations.json")
    second = build_calibration_proposal_pack(FIXTURE_DIR / "ready_for_review_recommendations.json")

    assert first.pack_id == second.pack_id
    assert [item.proposal_id for item in first.proposals] == [item.proposal_id for item in second.proposals]
    assert first.created_at == second.created_at == "1970-01-01T00:00:00+00:00"
