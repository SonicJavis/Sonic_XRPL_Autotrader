from __future__ import annotations

from pathlib import Path


def test_streamlit_navigation_uses_views_paths() -> None:
    content = Path("dashboard/streamlit_app.py").read_text(encoding="utf-8")
    assert '"views/production_dashboard.py"' in content
    assert '"views/safety_status.py"' in content
    assert '"views/governance_status.py"' in content
    assert '"dashboard/pages/production_dashboard.py"' not in content


def test_phase39_dashboard_is_archived_from_auto_pages() -> None:
    assert Path("dashboard/archive/phase39_campaign_dashboard.py").exists()
    assert not Path("dashboard/pages/phase39_campaign_dashboard.py").exists()
