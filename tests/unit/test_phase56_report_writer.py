import json

from sonic_xrpl.calibration_implementation_plan.planner import build_calibration_implementation_plan
from sonic_xrpl.calibration_implementation_plan.report_writer import write_implementation_reports


def test_report_writer_emits_deterministic_files(tmp_path):
    plan = build_calibration_implementation_plan(
        "reports/phase55/latest_calibration_approval_ledger.json",
        "tests/fixtures/calibration_implementation_plan/approved_change_requests.json",
    )
    generated = write_implementation_reports(
        plan,
        "reports/phase55/latest_calibration_approval_ledger.json",
        "tests/fixtures/calibration_implementation_plan/approved_change_requests.json",
        tmp_path,
    )
    json_path = tmp_path / "latest_calibration_implementation_plan.json"
    md_path = tmp_path / "latest_calibration_implementation_plan.md"
    preview_path = tmp_path / "latest_calibration_dry_run_preview.md"
    assert json_path.exists()
    assert md_path.exists()
    assert preview_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["created_at"] == "1970-01-01T00:00:00+00:00"
    assert "dry_run_preview_markdown" in generated
