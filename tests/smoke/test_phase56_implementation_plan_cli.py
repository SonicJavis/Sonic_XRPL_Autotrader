import subprocess
import sys


APPROVAL = "reports/phase55/latest_calibration_approval_ledger.json"
REQUESTS = "tests/fixtures/calibration_implementation_plan/approved_change_requests.json"


def run_cli(*args):
    return subprocess.run([sys.executable, "-m", "sonic_xrpl.cli.main", *args], text=True, capture_output=True, check=False)


def test_phase56_cli_help_includes_commands():
    result = run_cli("--help")
    assert result.returncode == 0
    assert "calibration-implementation-plan" in result.stdout
    assert "calibration-implementation-dry-run" in result.stdout
    assert "calibration-implementation-report" in result.stdout


def test_calibration_implementation_plan_cli():
    result = run_cli("calibration-implementation-plan", "--approval-ledger", APPROVAL, "--change-requests", REQUESTS)
    assert result.returncode == 0, result.stderr
    assert "Planning only      : True" in result.stdout
    assert "Live execution     : BLOCKED" in result.stdout


def test_calibration_implementation_dry_run_cli():
    result = run_cli("calibration-implementation-dry-run", "--approval-ledger", APPROVAL, "--change-requests", REQUESTS)
    assert result.returncode == 0, result.stderr
    assert "DRY RUN ONLY" in result.stdout
    assert "No file was changed." in result.stdout
    assert "Live execution: BLOCKED" in result.stdout


def test_calibration_implementation_report_cli(tmp_path):
    result = run_cli(
        "calibration-implementation-report",
        "--approval-ledger",
        APPROVAL,
        "--change-requests",
        REQUESTS,
        "--output-dir",
        str(tmp_path),
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "latest_calibration_implementation_plan.json").exists()
    assert (tmp_path / "latest_calibration_implementation_plan.md").exists()
    assert (tmp_path / "latest_calibration_dry_run_preview.md").exists()
