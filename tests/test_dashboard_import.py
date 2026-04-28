def test_dashboard_import_does_not_execute_ui() -> None:
    import dashboard.streamlit_app as app

    assert callable(app.main)
