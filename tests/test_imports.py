def test_refactor_imports_work() -> None:
    import app.main  # noqa: F401
    import app.execution.pipeline  # noqa: F401
    import app.xrpl_core.client  # noqa: F401
    import dashboard.streamlit_app  # noqa: F401
