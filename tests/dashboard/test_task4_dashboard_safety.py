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
    from dashboard.lib import safety_loader

    monkeypatch.setattr(safety_loader, "_load_json", lambda _: None)
    payload = safety_loader.load_safety_snapshot()
    assert payload["overall_status"] == "review"
    assert payload["checks"]["Audit Validator"]["status"] == "review"


def test_phase55_phase56_safe_artifacts_are_pass(monkeypatch) -> None:
    from dashboard.lib import safety_loader

    safe55 = {
        "records": [
            {
                "live_execution_allowed": False,
                "auto_apply_allowed": False,
                "runtime_mutation_allowed": False,
                "paper_only": True,
                "offline_only": True,
            }
        ]
    }
    safe56 = {
        "live_execution_allowed": False,
        "auto_apply_allowed": False,
        "runtime_mutation_allowed": False,
        "paper_only": True,
        "offline_only": True,
        "dry_run_only": True,
    }
    audit = {"overall_passed": True}
    dep = {"overall_status": "pass"}

    def fake_load(path):
        p = str(path)
        if p.endswith("phase55\\latest_calibration_approval_ledger.json"):
            return safe55
        if p.endswith("phase56\\latest_calibration_implementation_plan.json"):
            return safe56
        if p.endswith("artifacts\\audit_validator_report.json"):
            return audit
        if p.endswith("docs\\audit\\latest_dependency_audit.json"):
            return dep
        return None

    monkeypatch.setattr(safety_loader, "_load_json", fake_load)
    payload = safety_loader.load_safety_snapshot()
    assert payload["checks"]["Safety Scan"]["status"] == "pass"
    assert payload["checks"]["Kill Switch State"]["status"] == "pass"
    assert payload["overall_status"] == "pass"


def test_explicit_unsafe_flags_fail_hard(monkeypatch) -> None:
    from dashboard.lib import safety_loader

    unsafe55 = {
        "records": [
            {
                "live_execution_allowed": True,
                "paper_only": True,
            }
        ]
    }
    safe56 = {
        "live_execution_allowed": False,
        "auto_apply_allowed": False,
        "runtime_mutation_allowed": False,
        "paper_only": True,
        "offline_only": True,
        "dry_run_only": True,
    }
    audit = {"overall_passed": True}
    dep = {"overall_status": "pass"}

    def fake_load(path):
        p = str(path)
        if p.endswith("phase55\\latest_calibration_approval_ledger.json"):
            return unsafe55
        if p.endswith("phase56\\latest_calibration_implementation_plan.json"):
            return safe56
        if p.endswith("artifacts\\audit_validator_report.json"):
            return audit
        if p.endswith("docs\\audit\\latest_dependency_audit.json"):
            return dep
        return None

    monkeypatch.setattr(safety_loader, "_load_json", fake_load)
    payload = safety_loader.load_safety_snapshot()
    assert payload["checks"]["Safety Scan"]["status"] == "fail"
    assert payload["overall_status"] == "fail"
