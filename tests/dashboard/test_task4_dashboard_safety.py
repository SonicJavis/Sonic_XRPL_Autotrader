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
        Path("dashboard/views/production_dashboard.py").read_text(encoding="utf-8")
        + Path("dashboard/views/safety_status.py").read_text(encoding="utf-8")
        + Path("dashboard/views/governance_status.py").read_text(encoding="utf-8")
    ).lower()
    forbidden = ("st.button(", "submit_transaction", "submitandwait", "wallet_connect", "approve-and-apply", "xaman://")
    for token in forbidden:
        assert token not in content


def test_missing_artifacts_are_review_not_confirmed_pass_or_fail(monkeypatch) -> None:
    from dashboard import lib as _  # noqa: F401
    from dashboard.lib import safety_loader

    monkeypatch.setattr(safety_loader, "_load_json", lambda _: None)
    payload = safety_loader.load_safety_snapshot()
    assert payload["overall_status"] == "review"
    assert payload["checks"]["Audit Validator"]["status"] == "review"
