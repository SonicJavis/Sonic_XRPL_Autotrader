from __future__ import annotations


def test_task4_dashboard_imports_without_side_effect() -> None:
    import dashboard.streamlit_app as app
    import dashboard.pages.production_dashboard as production
    import dashboard.pages.safety_status as safety
    import dashboard.pages.governance_status as governance

    assert callable(app.main)
    assert callable(production.main)
    assert callable(safety.main)
    assert callable(governance.main)
