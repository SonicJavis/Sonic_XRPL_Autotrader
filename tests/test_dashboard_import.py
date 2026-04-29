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


def test_dashboard_live_observability_panel_is_review_only() -> None:
    from pathlib import Path

    source = Path("dashboard/streamlit_app.py").read_text(encoding="utf-8")

    assert "Ledger event-time drives validation windows" in source
    assert "Processing time is observability only" in source
    assert "No calibration setting is changed from this panel" in source
    assert "Derived from validated ledger data only" in source
    assert "Execution not guaranteed on XRPL" in source
    assert "Estimates based on current snapshot only" in source
    live_panel = source[source.index("XRPL Live Probabilistic Observatory") :]
    for phrase in ("execute trade", "auto trade", "wallet connect", "approve-and-apply"):
        assert phrase not in live_panel.lower()
