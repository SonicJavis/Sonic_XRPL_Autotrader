from sonic_xrpl.outcome_corpus import (
    DETERMINISTIC_GENERATED_AT,
    OutcomeCorpus,
    OutcomeReplayCase,
    PaperObservationPoint,
    build_outcome_corpus,
)


FIXTURE = "tests/fixtures/outcome_corpus/source_backed_multi_window.json"
MIXED_FIXTURE = "tests/fixtures/outcome_corpus/mixed_quality_observations.json"


def test_phase52_models_keep_paper_and_live_defaults():
    point = PaperObservationPoint(
        candidate_id="candidate",
        observed_at="",
        window_label="5m",
        reference_price=None,
        observed_price=None,
        observed_return_pct=None,
        liquidity_state=None,
        volume_state=None,
        source="fixture",
        source_url=None,
        source_backed=False,
        synthetic=False,
        limitations=["observed_at_missing"],
        missing_fields=["observed_at"],
    )
    replay_case = OutcomeReplayCase(
        replay_case_id="case",
        candidate_id="candidate",
        signal_id=None,
        review_id=None,
        paper_intent_id=None,
        observation_points=[point],
        windows_present=["5m"],
        windows_missing=["15m", "1h", "4h", "24h"],
        limitations=point.limitations,
        source_backed=False,
        synthetic=False,
    )

    assert point.paper_only is True
    assert replay_case.paper_only is True
    assert replay_case.live_execution_allowed is False


def test_phase52_corpus_defaults_block_live_execution():
    corpus = build_outcome_corpus([FIXTURE])

    assert isinstance(corpus, OutcomeCorpus)
    assert corpus.paper_only is True
    assert corpus.live_execution_allowed is False
    assert corpus.generated_at == DETERMINISTIC_GENERATED_AT
    assert all(case.live_execution_allowed is False for case in corpus.replay_cases)


def test_phase52_deterministic_ids_stable_across_repeated_builds():
    first = build_outcome_corpus([FIXTURE])
    second = build_outcome_corpus([FIXTURE])

    assert first.corpus_id == second.corpus_id
    assert [case.replay_case_id for case in first.replay_cases] == [
        case.replay_case_id for case in second.replay_cases
    ]


def test_phase52_missing_fields_are_preserved():
    corpus = build_outcome_corpus([MIXED_FIXTURE])
    points = [
        point
        for case in corpus.replay_cases
        for point in case.observation_points
        if point.candidate_id == "phase52_mixed_candidate_d" and point.window_label == "15m"
    ]

    assert points
    assert points[0].observed_at == ""
    assert "observed_at" in points[0].missing_fields
    assert "observed_at_missing" in points[0].limitations
