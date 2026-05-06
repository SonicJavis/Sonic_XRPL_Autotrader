from sonic_xrpl.signals.evidence import evidence_from_rows, load_candidate_rows


def test_unknown_observed_at_remains_unknown_and_limited():
    candidates = evidence_from_rows(load_candidate_rows("tests/fixtures/firstledger/unknown_observed_at.json"))
    assert len(candidates) == 1
    assert candidates[0].observed_at == ""
    assert "observed_at_missing" in candidates[0].limitations
    assert "observed_at" in candidates[0].raw_fields_missing


def test_no_fake_liquidity_holder_or_dev_hold_fields_are_invented():
    candidate = evidence_from_rows(load_candidate_rows("tests/fixtures/firstledger/source_backed_candidates.json"))[0]
    assert not hasattr(candidate, "liquidity")
    assert not hasattr(candidate, "holder_count")
    assert not hasattr(candidate, "dev_holdings")


def test_synthetic_fixture_is_labelled():
    candidate = evidence_from_rows(load_candidate_rows("tests/fixtures/firstledger/synthetic_candidates.json"))[0]
    assert candidate.synthetic is True
    assert "synthetic_fixture_not_real_market_data" in candidate.limitations
