import subprocess
import sys


PROPOSAL = "tests/fixtures/calibration_proposal/ready_for_review_recommendations.json"
REVIEW = "tests/fixtures/calibration_approval/approved_change_request.json"


def run_cli(*args):
    return subprocess.run([sys.executable, "-m", "sonic_xrpl.cli.main", *args], text=True, capture_output=True, check=False)


def test_phase55_cli_help_includes_commands():
    result = run_cli("--help")

    assert result.returncode == 0
    assert "calibration-approval-ledger" in result.stdout
    assert "calibration-change-requests" in result.stdout
    assert "calibration-approval-report" in result.stdout


def test_calibration_approval_ledger_cli():
    result = run_cli("calibration-approval-ledger", "--proposal-fixture", PROPOSAL, "--review-fixture", REVIEW)

    assert result.returncode == 0, result.stderr
    assert "Phase 55 approval ledger is offline, paper-only, and non-mutating." in result.stdout
    assert "No calibration changes are applied." in result.stdout
    assert "Live execution remains blocked." in result.stdout


def test_calibration_change_requests_cli():
    result = run_cli("calibration-change-requests", "--proposal-fixture", PROPOSAL, "--review-fixture", REVIEW)

    assert result.returncode == 0, result.stderr
    assert "Change requests are review artifacts only." in result.stdout
    assert "apply_allowed=False" in result.stdout
    assert "runtime_mutation_allowed=False" in result.stdout


def test_calibration_approval_report_cli(tmp_path):
    result = run_cli(
        "calibration-approval-report",
        "--proposal-fixture",
        PROPOSAL,
        "--review-fixture",
        REVIEW,
        "--output-dir",
        str(tmp_path),
    )

    assert result.returncode == 0, result.stderr
    assert (tmp_path / "latest_calibration_approval_ledger.json").exists()
    assert (tmp_path / "latest_calibration_approval_ledger.md").exists()
    assert (tmp_path / "latest_calibration_change_requests.json").exists()
    assert (tmp_path / "latest_calibration_change_requests.md").exists()
