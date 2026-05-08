from sonic_xrpl.outcome_corpus import CANONICAL_WINDOWS, build_outcome_corpus
from sonic_xrpl.outcome_corpus.loader import point_from_row


SOURCE_FIXTURE = "tests/fixtures/outcome_corpus/source_backed_multi_window.json"
MISSING_FIXTURE = "tests/fixtures/outcome_corpus/missing_windows.json"
SYNTHETIC_FIXTURE = "tests/fixtures/outcome_corpus/synthetic_observations.json"
MIXED_FIXTURE = "tests/fixtures/outcome_corpus/mixed_quality_observations.json"
EMPTY_FIXTURE = "tests/fixtures/outcome_corpus/empty_observations.json"


def test_phase52_builds_source_backed_multi_window_corpus():
    corpus = build_outcome_corpus([SOURCE_FIXTURE])

    assert corpus.total_cases == 1
    assert corpus.source_backed_cases == 1
    assert corpus.synthetic_cases == 0
    replay_case = corpus.replay_cases[0]
    assert replay_case.candidate_id == "phase52_source_candidate_a"
    assert replay_case.windows_present == tuple(CANONICAL_WINDOWS)
    assert replay_case.windows_missing == ()
    assert replay_case.source_backed is True
    assert replay_case.synthetic is False


def test_phase52_builder_groups_by_candidate_id():
    corpus = build_outcome_corpus([MIXED_FIXTURE])

    assert corpus.total_cases == 2
    assert {case.candidate_id for case in corpus.replay_cases} == {
        "phase52_mixed_candidate_d",
        "phase52_mixed_candidate_e",
    }


def test_phase52_builder_computes_present_and_missing_windows():
    corpus = build_outcome_corpus([MISSING_FIXTURE])
    replay_case = corpus.replay_cases[0]

    assert replay_case.windows_present == ("5m", "1h")
    assert replay_case.windows_missing == ("15m", "4h", "24h")


def test_phase52_builder_does_not_generate_timestamps_or_values():
    corpus = build_outcome_corpus([MIXED_FIXTURE])
    limited_point = next(
        point
        for case in corpus.replay_cases
        for point in case.observation_points
        if point.candidate_id == "phase52_mixed_candidate_d" and point.window_label == "15m"
    )

    assert limited_point.observed_at == ""
    assert limited_point.observed_price is None
    assert limited_point.observed_return_pct is None
    assert limited_point.source_url is None
    assert limited_point.liquidity_state == "unknown"


def test_phase52_builder_handles_empty_fixture_as_insufficient():
    corpus = build_outcome_corpus([EMPTY_FIXTURE])

    assert corpus.total_cases == 0
    assert corpus.quality_summary.quality_grade == "INSUFFICIENT"
    assert corpus.quality_summary.missing_observation_cases == 0


def test_phase52_builder_labels_synthetic_fixture():
    corpus = build_outcome_corpus([SYNTHETIC_FIXTURE])

    assert corpus.synthetic_cases == 1
    assert corpus.source_backed_cases == 0
    assert corpus.replay_cases[0].synthetic is True
    assert corpus.replay_cases[0].source_backed is False


def test_phase52_builder_reports_mixed_quality_partial_cases():
    corpus = build_outcome_corpus([MIXED_FIXTURE])

    assert corpus.quality_summary.partial_cases >= 1
    assert corpus.limited_cases >= 1
    assert "observed_at_missing" in corpus.quality_summary.limitation_counts


def test_phase52_loader_marks_invalid_numeric_observations_limited(tmp_path):
    point = point_from_row(
        {
            "candidate_id": "phase52_invalid_numeric_candidate",
            "observed_at": "2026-05-07T00:05:00+00:00",
            "window_label": "5m",
            "reference_price": "n/a",
            "observed_price": "0.0105",
            "observed_return_pct": "not-a-number",
            "source": "phase52_invalid_fixture",
            "source_url": "https://xrpl.org/docs/references/protocol/transactions/metadata",
            "source_backed": True,
            "synthetic": False,
            "limitations": [],
            "missing_fields": [],
        },
        tmp_path / "invalid_numeric.json",
    )

    assert point.reference_price is None
    assert point.observed_return_pct is None
    assert "reference_price" in point.missing_fields
    assert "invalid_numeric_field:reference_price" in point.limitations
    assert "invalid_numeric_field:observed_return_pct" in point.limitations
