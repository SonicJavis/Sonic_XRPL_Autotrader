from sonic_xrpl.outcome_corpus import build_outcome_corpus
from sonic_xrpl.outcome_corpus.builder import build_replay_case
from sonic_xrpl.outcome_corpus.loader import point_from_row
from sonic_xrpl.outcome_corpus.quality import summarize_quality


SOURCE_FIXTURE = "tests/fixtures/outcome_corpus/source_backed_multi_window.json"
MISSING_FIXTURE = "tests/fixtures/outcome_corpus/missing_windows.json"
SYNTHETIC_FIXTURE = "tests/fixtures/outcome_corpus/synthetic_observations.json"
EMPTY_FIXTURE = "tests/fixtures/outcome_corpus/empty_observations.json"


GRADE_RANK = {"INSUFFICIENT": 0, "D": 1, "C": 2, "B": 3, "A": 4}


def grade_rank(path: str) -> int:
    return GRADE_RANK[build_outcome_corpus([path]).quality_summary.quality_grade]


def test_phase52_complete_source_backed_fixture_gets_higher_grade():
    assert grade_rank(SOURCE_FIXTURE) > grade_rank(MISSING_FIXTURE)
    assert grade_rank(SOURCE_FIXTURE) > grade_rank(SYNTHETIC_FIXTURE)


def test_phase52_missing_windows_lower_grade():
    source = build_outcome_corpus([SOURCE_FIXTURE])
    missing = build_outcome_corpus([MISSING_FIXTURE])

    assert missing.quality_summary.quality_grade in {"C", "D"}
    assert missing.quality_summary.average_windows_present < source.quality_summary.average_windows_present


def test_phase52_synthetic_observations_lower_grade():
    synthetic = build_outcome_corpus([SYNTHETIC_FIXTURE])

    assert synthetic.quality_summary.quality_grade == "D"
    assert synthetic.quality_summary.synthetic_cases == 1


def test_phase52_empty_corpus_gets_insufficient():
    empty = build_outcome_corpus([EMPTY_FIXTURE])

    assert empty.quality_summary.quality_grade == "INSUFFICIENT"
    assert empty.quality_summary.recommendation == "Collect usable paper observation fixtures before running calibration review."


def test_phase52_quality_never_outputs_strategy_action_wording():
    for path in [SOURCE_FIXTURE, MISSING_FIXTURE, SYNTHETIC_FIXTURE, EMPTY_FIXTURE]:
        recommendation = build_outcome_corpus([path]).quality_summary.recommendation.lower()
        assert "buy" not in recommendation
        assert "sell" not in recommendation
        assert "avoid" not in recommendation
        assert "threshold" not in recommendation


def test_phase52_invalid_numeric_observations_are_not_complete(tmp_path):
    point = point_from_row(
        {
            "candidate_id": "phase52_invalid_numeric_candidate",
            "observed_at": "2026-05-07T00:05:00+00:00",
            "window_label": "5m",
            "reference_price": "n/a",
            "observed_price": "0.0105",
            "observed_return_pct": "not-a-number",
            "source": "phase52_invalid_fixture",
            "source_backed": True,
            "synthetic": False,
            "limitations": [],
            "missing_fields": [],
        },
        tmp_path / "invalid_numeric.json",
    )
    replay_case = build_replay_case("phase52_invalid_numeric_candidate", [point])
    quality = summarize_quality([replay_case])

    assert quality.complete_cases == 0
    assert quality.quality_grade != "A"
    assert "invalid_numeric_field:reference_price" in quality.limitation_counts
