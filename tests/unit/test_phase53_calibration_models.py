from sonic_xrpl.calibration_review import (
    build_threshold_recommendations,
    evaluate_readiness,
    load_evidence_snapshot,
)


FIXTURE = "tests/fixtures/calibration_review/sufficient_source_backed_evidence.json"


def test_phase53_models_default_to_paper_only_and_block_live_execution():
    snapshot = load_evidence_snapshot(FIXTURE)
    result = evaluate_readiness(snapshot)
    recommendations = build_threshold_recommendations(result)

    assert snapshot.paper_only is True
    assert snapshot.live_execution_allowed is False
    assert result.paper_only is True
    assert result.live_execution_allowed is False
    assert all(item.non_mutating is True for item in recommendations)
    assert all(item.requires_human_review is True for item in recommendations)
    assert all(item.live_execution_allowed is False for item in recommendations)


def test_phase53_ids_are_deterministic_for_same_fixture():
    first = load_evidence_snapshot(FIXTURE)
    second = load_evidence_snapshot(FIXTURE)
    first_result = evaluate_readiness(first)
    second_result = evaluate_readiness(second)
    first_recs = build_threshold_recommendations(first_result)
    second_recs = build_threshold_recommendations(second_result)

    assert first.snapshot_id == second.snapshot_id
    assert first.created_at == "1970-01-01T00:00:00+00:00"
    assert first_result.readiness_id == second_result.readiness_id
    assert [item.recommendation_id for item in first_recs] == [
        item.recommendation_id for item in second_recs
    ]
