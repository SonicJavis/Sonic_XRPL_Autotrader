import importlib


def test_dashboard_import_safe_for_xrpl_ingestion_panel() -> None:
    module = importlib.import_module("dashboard.streamlit_app")

    assert module is not None
