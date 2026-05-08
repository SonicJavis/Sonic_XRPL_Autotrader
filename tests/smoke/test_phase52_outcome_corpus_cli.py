import subprocess
import sys


FIXTURE = "tests/fixtures/outcome_corpus/source_backed_multi_window.json"


def run_cli(*args):
    return subprocess.run([sys.executable, "-m", "sonic_xrpl.cli.main", *args], text=True, capture_output=True, check=False)


def test_phase52_outcome_corpus_cli_offline():
    result = run_cli("outcome-corpus", "--fixture", FIXTURE)

    assert result.returncode == 0, result.stderr
    assert "Phase 52 Outcome Corpus" in result.stdout
    assert "Paper-only" in result.stdout
    assert "Offline" in result.stdout
    assert "Live execution    : BLOCKED" in result.stdout


def test_phase52_outcome_corpus_report_cli_writes_files(tmp_path):
    result = run_cli(
        "outcome-corpus-report",
        "--fixture",
        FIXTURE,
        "--output-dir",
        str(tmp_path),
    )

    assert result.returncode == 0, result.stderr
    assert (tmp_path / "outcome_corpus.json").exists()
    assert (tmp_path / "outcome_corpus.md").exists()
    assert (tmp_path / "outcome_corpus_quality.json").exists()
    assert (tmp_path / "outcome_corpus_quality.md").exists()
    assert "Live execution    : BLOCKED" in result.stdout


def test_phase52_outcome_corpus_quality_cli_prints_grade():
    result = run_cli("outcome-corpus-quality", "--fixture", FIXTURE)

    assert result.returncode == 0, result.stderr
    assert "Phase 52 Outcome Corpus Quality" in result.stdout
    assert "Quality grade" in result.stdout
    assert "Live execution    : BLOCKED" in result.stdout
