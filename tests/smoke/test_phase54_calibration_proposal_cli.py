import subprocess
import sys
from pathlib import Path


FIXTURE = "tests/fixtures/calibration_proposal/ready_for_review_recommendations.json"


def run_cli(*args):
    return subprocess.run([sys.executable, "-m", "sonic_xrpl.cli.main", *args], text=True, capture_output=True, check=False)


def test_phase54_cli_help_includes_new_commands():
    result = run_cli("--help")

    assert result.returncode == 0
    assert "calibration-proposals" in result.stdout
    assert "calibration-proposal-report" in result.stdout
    assert "calibration-proposal-diff" in result.stdout


def test_calibration_proposals_cli_works():
    result = run_cli("calibration-proposals", "--fixture", FIXTURE)

    assert result.returncode == 0, result.stderr
    assert "Phase 54 Calibration Proposals" in result.stdout
    assert "Paper-only calibration proposals" in result.stdout
    assert "Human review required" in result.stdout
    assert "No settings were changed" in result.stdout
    assert "Live execution is blocked" in result.stdout


def test_calibration_proposal_report_cli_writes_files(tmp_path):
    result = run_cli("calibration-proposal-report", "--fixture", FIXTURE, "--output-dir", str(tmp_path))

    assert result.returncode == 0, result.stderr
    assert (tmp_path / "calibration_proposal_pack.json").exists()
    assert (tmp_path / "calibration_proposal_pack.md").exists()
    assert "No settings were changed" in result.stdout


def test_calibration_proposal_diff_cli_prints_proposed_only():
    result = run_cli("calibration-proposal-diff", "--fixture", FIXTURE)

    assert result.returncode == 0, result.stderr
    assert "proposed only - not applied" in result.stdout
    assert "No settings were changed." in result.stdout
