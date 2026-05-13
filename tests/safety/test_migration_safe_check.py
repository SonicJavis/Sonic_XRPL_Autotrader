"""Phase 58C: tests for migration-safe control checks."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Import the script under test
# ---------------------------------------------------------------------------

sys.path.insert(0, str(REPO_ROOT / "scripts"))
import migration_safe_check as msc  # noqa: E402


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _all_results_pass(results: list[tuple[str, bool, str]]) -> list[tuple[str, bool, str]]:
    return [(k, p, m) for k, p, m in results if not p and not m.startswith("INFO:")]


# ---------------------------------------------------------------------------
# Basic presence tests
# ---------------------------------------------------------------------------

class TestRequiredDocsExist:
    def test_migration_safe_control_checks_doc_exists(self) -> None:
        assert (REPO_ROOT / "docs/MIGRATION_SAFE_CONTROL_CHECKS.md").exists()

    def test_migration_readiness_matrix_doc_exists(self) -> None:
        assert (REPO_ROOT / "docs/MIGRATION_READINESS_MATRIX.md").exists()

    def test_live_readiness_policy_doc_exists(self) -> None:
        assert (REPO_ROOT / "docs/LIVE_READINESS_POLICY.md").exists()

    def test_canonical_runtime_ownership_policy_doc_exists(self) -> None:
        assert (REPO_ROOT / "docs/CANONICAL_RUNTIME_OWNERSHIP_POLICY.md").exists()

    def test_policy_index_exists(self) -> None:
        assert (REPO_ROOT / "docs/POLICY_INDEX.md").exists()

    def test_safety_model_exists(self) -> None:
        assert (REPO_ROOT / "docs/SAFETY_MODEL.md").exists()


class TestRequiredRuntimeFilesExist:
    def test_app_main_present(self) -> None:
        assert (REPO_ROOT / "app/main.py").exists()

    def test_v2_cli_present(self) -> None:
        assert (REPO_ROOT / "src/sonic_xrpl/cli/main.py").exists()

    def test_live_guard_present(self) -> None:
        assert (REPO_ROOT / "src/sonic_xrpl/execution/live_guard.py").exists()

    def test_execution_guard_present(self) -> None:
        assert (REPO_ROOT / "app/execution/execution_guard.py").exists()


# ---------------------------------------------------------------------------
# Required phrases present in docs
# ---------------------------------------------------------------------------

class TestRequiredPhrases:
    def _read(self, rel: str) -> str:
        return (REPO_ROOT / rel).read_text(encoding="utf-8").lower()

    def test_migration_safe_control_checks_does_not_perform_migration(self) -> None:
        text = self._read("docs/MIGRATION_SAFE_CONTROL_CHECKS.md")
        assert "does not perform runtime migration" in text

    def test_migration_safe_control_checks_does_not_change_ownership(self) -> None:
        text = self._read("docs/MIGRATION_SAFE_CONTROL_CHECKS.md")
        assert "does not change runtime ownership" in text

    def test_migration_safe_control_checks_app_is_current_runtime(self) -> None:
        text = self._read("docs/MIGRATION_SAFE_CONTROL_CHECKS.md")
        assert "app/` remains the current runnable legacy api/paper runtime" in text

    def test_migration_safe_control_checks_v2_is_future_target(self) -> None:
        text = self._read("docs/MIGRATION_SAFE_CONTROL_CHECKS.md")
        assert "src/sonic_xrpl/` remains the canonical future runtime target" in text

    def test_migration_safe_control_checks_prototype_is_historical(self) -> None:
        text = self._read("docs/MIGRATION_SAFE_CONTROL_CHECKS.md")
        assert "execution_prototype/` remains historical/reference-only" in text

    def test_migration_safe_control_checks_requires_explicit_approval(self) -> None:
        text = self._read("docs/MIGRATION_SAFE_CONTROL_CHECKS.md")
        assert "explicit future phase approval" in text

    def test_migration_safe_control_checks_has_five_gates(self) -> None:
        text = self._read("docs/MIGRATION_SAFE_CONTROL_CHECKS.md")
        for gate in ("parity gates", "safety gates", "rollback gates", "docs gates", "audit gates"):
            assert gate in text, f"missing gate phrase: {gate}"

    def test_migration_safe_control_checks_cutover_separate_from_readiness(self) -> None:
        text = self._read("docs/MIGRATION_SAFE_CONTROL_CHECKS.md")
        assert "runtime cutover is separate from migration readiness" in text

    def test_migration_safe_control_checks_live_enablement_separate_from_migration(self) -> None:
        text = self._read("docs/MIGRATION_SAFE_CONTROL_CHECKS.md")
        assert "live enablement is separate from runtime migration" in text

    def test_migration_safe_control_checks_confirms_no_live_execution(self) -> None:
        text = self._read("docs/MIGRATION_SAFE_CONTROL_CHECKS.md")
        assert "still no live execution" in text

    def test_migration_readiness_matrix_no_cutover_performed(self) -> None:
        text = self._read("docs/MIGRATION_READINESS_MATRIX.md")
        assert "no runtime cutover is performed here" in text

    def test_migration_readiness_matrix_no_live_execution_authorized(self) -> None:
        text = self._read("docs/MIGRATION_READINESS_MATRIX.md")
        assert "live execution is not authorized here" in text

    def test_migration_readiness_matrix_has_blocked_not_started(self) -> None:
        text = self._read("docs/MIGRATION_READINESS_MATRIX.md")
        assert "blocked/not-started" in text

    def test_migration_readiness_matrix_has_not_cutover_rows(self) -> None:
        text = self._read("docs/MIGRATION_READINESS_MATRIX.md")
        assert "not-cutover" in text


# ---------------------------------------------------------------------------
# Prohibited live-authorization phrases must be ABSENT
# ---------------------------------------------------------------------------

class TestProhibitedPhrases:
    DOCS_TO_CHECK = [
        "docs/MIGRATION_SAFE_CONTROL_CHECKS.md",
        "docs/MIGRATION_READINESS_MATRIX.md",
        "docs/LIVE_READINESS_POLICY.md",
        "docs/CANONICAL_RUNTIME_OWNERSHIP_POLICY.md",
        "docs/POLICY_INDEX.md",
    ]

    PROHIBITED = [
        "live execution is authorized",
        "live trading is authorized",
        "phase 58c authorizes live",
        "phase 58c enables live",
        "migration is complete",
        "cutover is complete",
        "runtime cutover is authorized",
    ]

    @pytest.mark.parametrize("doc", DOCS_TO_CHECK)
    @pytest.mark.parametrize("phrase", PROHIBITED)
    def test_prohibited_phrase_absent(self, doc: str, phrase: str) -> None:
        text = (REPO_ROOT / doc).read_text(encoding="utf-8").lower()
        assert phrase not in text, f"prohibited phrase found in {doc}: {phrase!r}"


# ---------------------------------------------------------------------------
# Script check functions
# ---------------------------------------------------------------------------

class TestScriptCheckFunctions:
    def test_check_required_docs_passes_for_current_repo(self) -> None:
        results: list[tuple[str, bool, str]] = []
        msc.check_required_docs(results)
        failures = _all_results_pass(results)
        assert not failures, f"doc check failures: {failures}"

    def test_check_required_runtime_files_passes_for_current_repo(self) -> None:
        results: list[tuple[str, bool, str]] = []
        msc.check_required_runtime_files(results)
        failures = _all_results_pass(results)
        assert not failures, f"runtime file check failures: {failures}"

    def test_check_required_phrases_passes_for_current_repo(self) -> None:
        results: list[tuple[str, bool, str]] = []
        msc.check_required_phrases(results)
        failures = _all_results_pass(results)
        assert not failures, f"phrase check failures: {failures}"

    def test_check_prohibited_phrases_passes_for_current_repo(self) -> None:
        results: list[tuple[str, bool, str]] = []
        msc.check_prohibited_phrases(results)
        failures = _all_results_pass(results)
        assert not failures, f"prohibited-phrase check failures: {failures}"

    def test_run_checks_passes_for_current_repo(self) -> None:
        results = msc.run_checks()
        failures = _all_results_pass(results)
        assert not failures, f"run_checks failures: {failures}"

    def test_main_returns_zero_for_current_repo(self) -> None:
        results = msc.run_checks()
        passed = msc.emit_report(results)
        assert passed, "main() should return 0 for the current repo state"


# ---------------------------------------------------------------------------
# Missing-doc failure tests (using tmp_path)
# ---------------------------------------------------------------------------

class TestMissingDocFails:
    def test_missing_doc_produces_failure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(msc, "REPO_ROOT", tmp_path)
        results: list[tuple[str, bool, str]] = []
        msc.check_required_docs(results)
        failures = _all_results_pass(results)
        assert failures, "should fail when required docs are missing"

    def test_missing_runtime_file_produces_failure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(msc, "REPO_ROOT", tmp_path)
        results: list[tuple[str, bool, str]] = []
        msc.check_required_runtime_files(results)
        failures = _all_results_pass(results)
        assert failures, "should fail when runtime files are missing"

    def test_missing_phrase_produces_failure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        doc_path = tmp_path / "docs"
        doc_path.mkdir(parents=True)
        # Create a doc with wrong content so phrase check fails
        (doc_path / "MIGRATION_SAFE_CONTROL_CHECKS.md").write_text("placeholder", encoding="utf-8")
        (doc_path / "MIGRATION_READINESS_MATRIX.md").write_text("placeholder", encoding="utf-8")
        (doc_path / "LIVE_READINESS_POLICY.md").write_text("placeholder", encoding="utf-8")
        (doc_path / "CANONICAL_RUNTIME_OWNERSHIP_POLICY.md").write_text("placeholder", encoding="utf-8")
        (doc_path / "POLICY_INDEX.md").write_text("placeholder", encoding="utf-8")
        (doc_path / "SAFETY_MODEL.md").write_text("placeholder", encoding="utf-8")
        monkeypatch.setattr(msc, "REPO_ROOT", tmp_path)
        results: list[tuple[str, bool, str]] = []
        msc.check_required_phrases(results)
        failures = _all_results_pass(results)
        assert failures, "should fail when required phrases are missing"

    def test_prohibited_phrase_in_doc_produces_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        doc_path = tmp_path / "docs"
        doc_path.mkdir(parents=True)
        bad_content = "live execution is authorized here."
        (doc_path / "MIGRATION_SAFE_CONTROL_CHECKS.md").write_text(bad_content, encoding="utf-8")
        (doc_path / "MIGRATION_READINESS_MATRIX.md").write_text("ok", encoding="utf-8")
        (doc_path / "LIVE_READINESS_POLICY.md").write_text("ok", encoding="utf-8")
        (doc_path / "CANONICAL_RUNTIME_OWNERSHIP_POLICY.md").write_text("ok", encoding="utf-8")
        (doc_path / "POLICY_INDEX.md").write_text("ok", encoding="utf-8")
        (doc_path / "SAFETY_MODEL.md").write_text("ok", encoding="utf-8")
        monkeypatch.setattr(msc, "REPO_ROOT", tmp_path)
        results: list[tuple[str, bool, str]] = []
        msc.check_prohibited_phrases(results)
        failures = _all_results_pass(results)
        assert failures, "should fail when prohibited phrase is found in a doc"


# ---------------------------------------------------------------------------
# Report output test
# ---------------------------------------------------------------------------

class TestReportOutput:
    def test_report_includes_key_surfaces(self, capsys: pytest.CaptureFixture[str]) -> None:
        results = msc.run_checks()
        msc.emit_report(results)
        captured = capsys.readouterr()
        output = captured.out
        assert "Migration-Safe Control Check" in output
        assert "still no live execution" in output.lower()

    def test_report_all_pass_exits_true(self) -> None:
        results = msc.run_checks()
        passed = msc.emit_report(results)
        assert passed is True

    def test_report_with_failure_exits_false(self, capsys: pytest.CaptureFixture[str]) -> None:
        bad_results = [("key", False, "FAIL: something wrong")]
        passed = msc.emit_report(bad_results)
        assert passed is False


# ---------------------------------------------------------------------------
# No network / no mutation guarantees
# ---------------------------------------------------------------------------

class TestScriptSafety:
    def test_script_has_no_network_imports(self) -> None:
        script_path = REPO_ROOT / "scripts" / "migration_safe_check.py"
        text = script_path.read_text(encoding="utf-8")
        for forbidden in ("import requests", "import httpx", "import urllib.request", "import socket"):
            assert forbidden not in text, f"network import found: {forbidden}"

    def test_script_has_no_write_calls(self) -> None:
        script_path = REPO_ROOT / "scripts" / "migration_safe_check.py"
        text = script_path.read_text(encoding="utf-8")
        for forbidden in (".write(", ".write_text(", "open(", "shutil."):
            assert forbidden not in text, f"file-write call found: {forbidden}"

    def test_script_has_no_subprocess_calls(self) -> None:
        script_path = REPO_ROOT / "scripts" / "migration_safe_check.py"
        text = script_path.read_text(encoding="utf-8")
        assert "subprocess" not in text, "subprocess import found — script must be self-contained"
