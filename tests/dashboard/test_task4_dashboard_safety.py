from __future__ import annotations

from pathlib import Path

from dashboard.lib.safety_loader import load_safety_snapshot


def test_safety_loader_not_green_if_required_artifact_missing(monkeypatch) -> None:
    original_exists = Path.exists

    def fake_exists(self: Path) -> bool:
        if str(self).endswith("audit_validator_report.json"):
            return False
        return original_exists(self)

    monkeypatch.setattr(Path, "exists", fake_exists)
    payload = load_safety_snapshot()
    assert payload["overall_status"] != "pass"


def test_dashboard_pages_do_not_contain_execution_controls() -> None:
    content = (
        Path("dashboard/pages/production_dashboard.py").read_text(encoding="utf-8")
        + Path("dashboard/pages/safety_status.py").read_text(encoding="utf-8")
        + Path("dashboard/pages/governance_status.py").read_text(encoding="utf-8")
    ).lower()
    forbidden = ("st.button(", "submit_transaction", "submitandwait", "wallet_connect", "approve-and-apply", "xaman://")
    for token in forbidden:
        assert token not in content
