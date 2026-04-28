from app.validation.report_engine import UncertaintyReportEngine, ValidationSample


def test_high_disagreement_recommends_hardening() -> None:
    report = UncertaintyReportEngine().build(
        [
            ValidationSample("USD.rA", 0.8, True, 0.7, False),
            ValidationSample("USD.rA", 0.7, False, 0.6, False),
            ValidationSample("EUR.rB", 0.65, True, 0.65, False),
        ]
    )
    assert report.disagreement_score >= 0.5
    assert report.recommendation == "HARDEN_ASSUMPTIONS"


def test_low_confidence_recommends_collecting_more_data() -> None:
    report = UncertaintyReportEngine().build(
        [
            ValidationSample("USD.rA", 0.25, False, 0.2, True),
            ValidationSample("EUR.rB", 0.22, False, 0.3, True),
            ValidationSample("JPY.rC", 0.18, False, 0.35, True),
        ]
    )
    assert report.observation_confidence_avg <= 0.4
    assert report.recommendation == "COLLECT_MORE_DATA"


def test_stable_low_disagreement_recommends_hold() -> None:
    report = UncertaintyReportEngine().build(
        [
            ValidationSample("USD.rA", 0.10, False, 0.7, True),
            ValidationSample("USD.rA", 0.15, False, 0.8, True),
            ValidationSample("EUR.rB", 0.12, False, 0.75, True),
        ]
    )
    assert report.disagreement_score <= 0.25
    assert report.recommendation == "HOLD"
