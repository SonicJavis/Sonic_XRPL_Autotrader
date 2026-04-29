def test_dashboard_import_does_not_execute_ui() -> None:
    import dashboard.streamlit_app as app

    assert callable(app.main)


def test_dashboard_validation_wording_is_uncertainty_framed() -> None:
    from pathlib import Path

    source = Path("dashboard/streamlit_app.py").read_text(encoding="utf-8")

    assert "Validation reflects observed disagreement under uncertainty" in source
    assert "Observed outcomes are probabilistic" in source
    assert "XRPL Calibration Recommendations - Human Review" in source
    assert "Review surface only; no settings are changed" in source
    assert "Each item is a suggested review for a probabilistic outcome" in source
    assert "No transaction executed" in source or "No XRPL transaction is created or submitted" in source
