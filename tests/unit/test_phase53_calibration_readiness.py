from sonic_xrpl.calibration_review import evaluate_readiness, load_evidence_snapshot


BASE = "tests/fixtures/calibration_review"


def readiness(name: str):
    return evaluate_readiness(load_evidence_snapshot(f"{BASE}/{name}.json"))


def test_phase53_sufficient_source_backed_evidence_ready_for_human_review():
    result = readiness("sufficient_source_backed_evidence")

    assert result.status == "READY_FOR_HUMAN_REVIEW"
    assert result.blockers == ()
    assert result.confidence == 1.0


def test_phase53_insufficient_evidence_not_ready():
    result = readiness("insufficient_evidence")

    assert result.status == "NOT_READY"
    assert any("Corpus cases 0" in item for item in result.blockers)
    assert any("Attributed outcomes 0" in item for item in result.blockers)


def test_phase53_synthetic_heavy_cannot_be_ready():
    result = readiness("synthetic_heavy_evidence")

    assert result.status == "NOT_READY"
    assert any("Synthetic corpus cases" in item for item in result.blockers)


def test_phase53_missing_observations_lower_readiness():
    result = readiness("missing_observations")

    assert result.status in {"NEEDS_MORE_EVIDENCE", "REVIEW_WITH_CAUTION"}
    assert result.warnings
    assert any("Missing observation ratio" in item for item in result.warnings)


def test_phase53_invalid_numeric_observations_block_readiness():
    result = readiness("invalid_observations")

    assert result.status == "NEEDS_MORE_EVIDENCE"
    assert any("Invalid numeric observations" in item for item in result.blockers)


def test_phase53_live_enabled_inputs_block_readiness():
    result = readiness("live_enabled_blocker")

    assert result.status == "NEEDS_MORE_EVIDENCE"
    assert any("live execution blocked" in item for item in result.blockers)


def test_phase53_sparse_classes_warn_not_block():
    result = readiness("sparse_signal_classes")

    assert result.status == "REVIEW_WITH_CAUTION"
    assert any("Sparse signal classes" in item for item in result.warnings)
