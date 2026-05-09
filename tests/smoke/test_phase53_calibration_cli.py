import subprocess
import sys


FIXTURE = "tests/fixtures/calibration_review/sufficient_source_backed_evidence.json"


def run_cli(*args):
    return subprocess.run([sys.executable, "-m", "sonic_xrpl.cli.main", *args], text=True, capture_output=True, check=False)


def test_phase53_calibration_readiness_cli():
    result = run_cli("calibration-readiness", "--fixture", FIXTURE)

    assert result.returncode == 0, result.stderr
    assert "Phase 53 Calibration Readiness" in result.stdout
    assert "Paper-only" in result.stdout
    assert "Live execution    : BLOCKED" in result.stdout
    assert "Runtime mutation  : BLOCKED" in result.stdout
    assert "READY_FOR_HUMAN_REVIEW" in result.stdout


def test_phase53_calibration_recommendations_cli():
    result = run_cli("calibration-recommendations", "--fixture", FIXTURE)

    assert result.returncode == 0, result.stderr
    assert "Phase 53 Calibration Recommendations" in result.stdout
    assert "Advisory only" in result.stdout
    assert "non_mutating=True" in result.stdout


def test_phase53_calibration_readiness_report_cli_writes_files(tmp_path):
    result = run_cli(
        "calibration-readiness-report",
        "--fixture",
        FIXTURE,
        "--output-dir",
        str(tmp_path),
    )

    assert result.returncode == 0, result.stderr
    assert (tmp_path / "calibration_readiness.json").exists()
    assert (tmp_path / "calibration_readiness.md").exists()
    assert (tmp_path / "calibration_recommendations.json").exists()
    assert "Live execution    : BLOCKED" in result.stdout
