from pathlib import Path


def test_validation_surface_avoids_unsafe_certainty_language() -> None:
    files = [
        *Path("app/validation").glob("xrpl_*.py"),
        Path("app/api/routes_validation.py"),
        Path("dashboard/streamlit_app.py"),
        Path("scripts/xrpl_shadow_dry_run.py"),
    ]
    for path in files:
        text = path.read_text(encoding="utf-8").lower()
        for phrase in _UNSAFE_PHRASES:
            assert phrase not in text, f"{phrase!r} found in {path}"


def test_validation_surface_keeps_uncertainty_framing() -> None:
    dashboard = Path("dashboard/streamlit_app.py").read_text(encoding="utf-8")
    api = Path("app/api/routes_validation.py").read_text(encoding="utf-8")

    assert "No ground truth exists" in dashboard
    assert "Observed outcomes are probabilistic" in dashboard
    assert "Validation reflects observed disagreement under uncertainty" in dashboard
    assert "Each item is a suggested review for a probabilistic outcome" in dashboard
    assert "No ground truth exists" in api


_UNSAFE_PHRASES = (
    "true fill",
    "actual fill",
    "guaranteed fill",
    "guaranteed execution",
    "real execution",
    "executable truth",
    "proven executable",
    "confirmed fill",
)
