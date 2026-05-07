import subprocess
import sys


def run_cli(*args):
    return subprocess.run([sys.executable, "-m", "sonic_xrpl.cli.main", *args], text=True, capture_output=True, check=False)


def test_phase51_paper_outcomes_cli_offline():
    result = run_cli(
        "paper-outcomes",
        "--signals-fixture",
        "tests/fixtures/firstledger/source_backed_candidates.json",
        "--outcomes-fixture",
        "tests/fixtures/outcomes/paper_observations.json",
    )
    assert result.returncode == 0, result.stderr
    assert "Phase 51 Paper Outcomes" in result.stdout
    assert "Live execution    : BLOCKED" in result.stdout
    assert "fixture_source_backed_watch" in result.stdout
    assert "live_execution_allowed=False" in result.stdout


def test_phase51_report_clis_write_files(tmp_path):
    outcome_result = run_cli(
        "paper-outcome-report",
        "--signals-fixture",
        "tests/fixtures/firstledger/source_backed_candidates.json",
        "--outcomes-fixture",
        "tests/fixtures/outcomes/paper_observations.json",
        "--output-dir",
        str(tmp_path),
    )
    assert outcome_result.returncode == 0, outcome_result.stderr
    assert (tmp_path / "phase51_paper_outcomes.json").exists()
    assert (tmp_path / "phase51_paper_outcomes.md").exists()

    feedback_result = run_cli(
        "signal-feedback-report",
        "--signals-fixture",
        "tests/fixtures/firstledger/source_backed_candidates.json",
        "--outcomes-fixture",
        "tests/fixtures/outcomes/paper_observations.json",
        "--output-dir",
        str(tmp_path),
    )
    assert feedback_result.returncode == 0, feedback_result.stderr
    assert (tmp_path / "phase51_signal_feedback.json").exists()
    assert (tmp_path / "phase51_signal_feedback.md").exists()
