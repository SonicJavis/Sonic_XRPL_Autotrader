from sonic_xrpl.calibration_implementation_plan.dry_run_patch import render_dry_run_preview
from sonic_xrpl.calibration_implementation_plan.planner import build_calibration_implementation_plan


def test_dry_run_preview_contains_required_safety_text():
    plan = build_calibration_implementation_plan(
        "reports/phase55/latest_calibration_approval_ledger.json",
        "tests/fixtures/calibration_implementation_plan/approved_change_requests.json",
    )
    preview = render_dry_run_preview(plan.implementation_items)
    assert "DRY RUN ONLY" in preview
    assert "No file was changed." in preview
    assert "Live execution: BLOCKED" in preview
