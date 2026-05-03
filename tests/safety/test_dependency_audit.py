"""Tests for Phase 48 dependency audit logic.

All tests are offline — no live XRPL network access, no pip-audit network
calls. pip-audit is mocked where necessary to avoid vulnerability DB access.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Import helpers — make script importable regardless of sys.path
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dependency_audit import (  # noqa: E402
    COMPROMISED_XRPL_JS_VERSIONS,
    EXCLUDED_DIRS,
    NODE_DEP_FILES,
    PYTHON_DEP_FILES,
    build_report,
    check_node_dependencies,
    check_pip,
    check_pip_audit,
    check_python_dep_files,
    write_json_report,
    write_md_report,
)

# ---------------------------------------------------------------------------
# 1. Compromised xrpl.js version detection
# ---------------------------------------------------------------------------


class TestCompromisedXrplJsVersions:
    """Tests that compromised xrpl.js versions are detected in Node files."""

    COMPROMISED = ["4.2.1", "4.2.2", "4.2.3", "4.2.4", "2.14.2"]
    SAFE = ["4.2.5", "2.14.3", "4.3.0", "2.14.4", "4.5.0"]

    @pytest.fixture()
    def tmp_repo(self, tmp_path: Path) -> Path:
        """Create a minimal tmp repo directory."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname='test'")
        return tmp_path

    def _write_package_json(self, repo: Path, version: str) -> None:
        pkg = {"dependencies": {"xrpl": version}}
        (repo / "package.json").write_text(json.dumps(pkg))

    def _write_lockfile(self, repo: Path, version: str) -> None:
        # Simulate a package-lock.json that contains the version string
        content = f'{{"packages": {{"node_modules/xrpl": {{"version": "{version}"}}}}}}'
        (repo / "package-lock.json").write_text(content)

    @pytest.mark.parametrize("version", COMPROMISED)
    def test_compromised_version_detected_in_package_json(
        self, tmp_repo: Path, version: str
    ) -> None:
        self._write_package_json(tmp_repo, version)
        result = check_node_dependencies(tmp_repo)
        assert result["status"] == "fail", f"Expected fail for compromised {version}"
        assert not result["passed"]
        assert version in result["message"]

    @pytest.mark.parametrize("version", SAFE)
    def test_safe_version_not_flagged_in_package_json(
        self, tmp_repo: Path, version: str
    ) -> None:
        self._write_package_json(tmp_repo, version)
        result = check_node_dependencies(tmp_repo)
        assert result["status"] != "fail", f"Expected pass/info for safe {version}"
        assert result["passed"]

    @pytest.mark.parametrize("version", COMPROMISED)
    def test_compromised_version_detected_in_lockfile(
        self, tmp_repo: Path, version: str
    ) -> None:
        # Write a fake package.json so we have a Node context, plus the lockfile
        (tmp_repo / "package.json").write_text('{"dependencies":{}}')
        self._write_lockfile(tmp_repo, version)
        result = check_node_dependencies(tmp_repo)
        assert result["status"] == "fail", f"Expected fail for compromised lockfile {version}"

    @pytest.mark.parametrize("version", COMPROMISED)
    def test_package_json_with_caret_prefix(self, tmp_repo: Path, version: str) -> None:
        """Version specifiers like ^4.2.1 should still be detected."""
        self._write_package_json(tmp_repo, f"^{version}")
        result = check_node_dependencies(tmp_repo)
        assert result["status"] == "fail"

    @pytest.mark.parametrize("version", COMPROMISED)
    def test_package_json_with_tilde_prefix(self, tmp_repo: Path, version: str) -> None:
        self._write_package_json(tmp_repo, f"~{version}")
        result = check_node_dependencies(tmp_repo)
        assert result["status"] == "fail"

    def test_compromised_version_set_contains_all_five(self) -> None:
        assert COMPROMISED_XRPL_JS_VERSIONS == {
            "4.2.1", "4.2.2", "4.2.3", "4.2.4", "2.14.2"
        }


# ---------------------------------------------------------------------------
# 2. Missing Node files → not_applicable, not failure
# ---------------------------------------------------------------------------


class TestMissingNodeFiles:
    """When no Node files exist, audit returns not_applicable."""

    def test_no_node_files_returns_not_applicable(self, tmp_path: Path) -> None:
        result = check_node_dependencies(tmp_path)
        assert result["status"] == "not_applicable"
        assert result["passed"] is True
        assert "not_applicable" in result["status"]

    def test_no_node_files_message_is_informative(self, tmp_path: Path) -> None:
        result = check_node_dependencies(tmp_path)
        msg = result["message"].lower()
        assert "node" in msg or "not applicable" in msg

    def test_excluded_dirs_not_scanned(self, tmp_path: Path) -> None:
        """Excluded directories are documented in EXCLUDED_DIRS."""
        assert ".ecc-source" in EXCLUDED_DIRS
        assert ".venv" in EXCLUDED_DIRS
        assert ".git" in EXCLUDED_DIRS
        assert "artifacts" in EXCLUDED_DIRS


# ---------------------------------------------------------------------------
# 3. pip check command wrapper
# ---------------------------------------------------------------------------


class TestPipCheck:
    """Tests for pip check wrapper."""

    def test_pip_check_success(self) -> None:
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="No broken requirements found.\n",
                stderr="",
            )
            result = check_pip()
        assert result["passed"] is True
        assert result["status"] == "pass"

    def test_pip_check_failure(self) -> None:
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="fakepkg 1.0 requires brokenlib>=2.0, which is not installed.\n",
                stderr="",
            )
            result = check_pip()
        assert result["passed"] is False
        assert result["status"] == "fail"

    def test_pip_check_exception_handled(self) -> None:
        with patch("subprocess.run", side_effect=OSError("pip not found")):
            result = check_pip()
        assert result["passed"] is False
        assert result["status"] == "fail"
        assert "pip not found" in result["message"]


# ---------------------------------------------------------------------------
# 4. pip-audit wrapper (mocked — no real network calls)
# ---------------------------------------------------------------------------


class TestPipAudit:
    """Tests for pip-audit wrapper — network is mocked throughout."""

    def test_skip_flag_returns_skipped(self) -> None:
        result = check_pip_audit(skip=True)
        assert result["status"] == "skipped"
        assert result["passed"] is True

    def test_pip_audit_unavailable_returns_warning(self) -> None:
        with patch("subprocess.run") as mock_run:
            # probe import fails
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="No module named pip_audit")
            result = check_pip_audit()
        assert result["status"] == "warning"
        assert result["passed"] is True
        assert "pip-audit is not installed" in result["message"]

    def test_pip_audit_no_vulns_returns_pass(self) -> None:
        audit_json = json.dumps({"dependencies": [
            {"name": "xrpl-py", "version": "4.5.0", "vulns": []}
        ]})
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="", stderr=""),   # probe succeeds
                MagicMock(returncode=0, stdout=audit_json, stderr=""),  # audit pass
            ]
            result = check_pip_audit()
        assert result["status"] == "pass"
        assert result["passed"] is True
        assert result["vulnerabilities"] == []

    def test_pip_audit_known_vuln_returns_fail(self) -> None:
        vuln_json = json.dumps({"dependencies": [
            {
                "name": "fakepkg",
                "version": "1.0.0",
                "vulns": [{"id": "PYSEC-2024-999", "description": "Remote code execution"}],
            }
        ]})
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="", stderr=""),   # probe
                MagicMock(returncode=1, stdout=vuln_json, stderr=""),  # audit fail
            ]
            result = check_pip_audit()
        assert result["status"] == "fail"
        assert result["passed"] is False
        assert len(result["vulnerabilities"]) == 1

    def test_pip_audit_network_timeout_returns_warning(self) -> None:
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="", stderr=""),   # probe
                subprocess.TimeoutExpired(cmd="pip_audit", timeout=120),
            ]
            result = check_pip_audit()
        assert result["status"] == "warning"
        assert result["passed"] is True
        assert "timed out" in result["message"]

    def test_pip_audit_db_unavailable_returns_warning(self) -> None:
        """Non-zero exit but empty/unparseable output → network/DB issue → warning."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="", stderr=""),   # probe
                MagicMock(returncode=1, stdout="", stderr="Connection refused"),
            ]
            result = check_pip_audit()
        assert result["status"] == "warning"
        assert result["passed"] is True


# ---------------------------------------------------------------------------
# 5. Report structure
# ---------------------------------------------------------------------------


class TestReportStructure:
    """Tests for the report structure."""

    def _make_pass_pip(self) -> dict:
        return {"status": "pass", "passed": True, "message": "ok", "exit_code": 0}

    def _make_pass_pa(self) -> dict:
        return {"status": "pass", "passed": True, "message": "ok", "vulnerabilities": []}

    def _make_na_node(self) -> dict:
        return {
            "status": "not_applicable",
            "passed": True,
            "message": "no node files",
            "findings": [],
            "warnings": [],
        }

    def _make_python_files(self) -> dict:
        return {"status": "info", "passed": True, "message": "ok", "files_found": []}

    def test_report_contains_required_keys(self) -> None:
        report = build_report(
            self._make_pass_pip(),
            self._make_pass_pa(),
            self._make_na_node(),
            self._make_python_files(),
        )
        required = {
            "overall_status",
            "python_dependency_check",
            "pip_audit",
            "node_dependency_check",
            "findings",
            "warnings",
            "generated_at",
        }
        assert required.issubset(set(report.keys()))

    def test_report_pass_when_all_pass(self) -> None:
        report = build_report(
            self._make_pass_pip(),
            self._make_pass_pa(),
            self._make_na_node(),
            self._make_python_files(),
        )
        assert report["overall_status"] == "pass"

    def test_report_fail_when_pip_check_fails(self) -> None:
        pip_fail = {"status": "fail", "passed": False, "message": "broken deps", "exit_code": 1}
        report = build_report(pip_fail, self._make_pass_pa(), self._make_na_node(), self._make_python_files())
        assert report["overall_status"] == "fail"

    def test_report_fail_when_compromised_node(self) -> None:
        node_fail = {
            "status": "fail",
            "passed": False,
            "message": "COMPROMISED xrpl@4.2.1",
            "findings": [{"severity": "critical", "message": "COMPROMISED xrpl@4.2.1"}],
            "warnings": [],
        }
        report = build_report(self._make_pass_pip(), self._make_pass_pa(), node_fail, self._make_python_files())
        assert report["overall_status"] == "fail"

    def test_report_warning_when_pip_audit_unavailable(self) -> None:
        pa_warn = {
            "status": "warning",
            "passed": True,
            "message": "pip-audit is not installed",
            "vulnerabilities": [],
        }
        report = build_report(self._make_pass_pip(), pa_warn, self._make_na_node(), self._make_python_files())
        assert report["overall_status"] == "warning"

    def test_report_fail_when_pip_audit_finds_vuln(self) -> None:
        pa_fail = {
            "status": "fail",
            "passed": False,
            "message": "1 vulnerability found",
            "vulnerabilities": [{"name": "bad", "version": "1.0", "id": "X-1", "description": "oops"}],
        }
        report = build_report(self._make_pass_pip(), pa_fail, self._make_na_node(), self._make_python_files())
        assert report["overall_status"] == "fail"


# ---------------------------------------------------------------------------
# 6. Write reports
# ---------------------------------------------------------------------------


class TestReportWriting:
    """Tests that reports are written correctly."""

    def _base_report(self) -> dict:
        return {
            "schema_version": "1.0",
            "generated_at": "2026-05-03T00:00:00+00:00",
            "phase": "48",
            "overall_status": "pass",
            "python_dependency_check": {"status": "pass", "passed": True, "message": "ok", "exit_code": 0},
            "pip_audit": {"status": "pass", "passed": True, "message": "ok", "vulnerabilities": []},
            "node_dependency_check": {
                "status": "not_applicable",
                "passed": True,
                "message": "no node files",
                "findings": [],
                "warnings": [],
            },
            "python_dependency_files": {"status": "info", "passed": True, "message": "ok", "files_found": []},
            "findings": [],
            "warnings": [],
        }

    def test_write_json_report(self, tmp_path: Path) -> None:
        report = self._base_report()
        out = write_json_report(report, tmp_path)
        assert out.exists()
        data = json.loads(out.read_text())
        assert data["overall_status"] == "pass"
        assert data["phase"] == "48"

    def test_write_md_report(self, tmp_path: Path) -> None:
        report = self._base_report()
        out = write_md_report(report, tmp_path)
        assert out.exists()
        content = out.read_text()
        assert "Phase 48" in content
        assert "overall_status" in content.lower() or "PASS" in content

    def test_reports_go_to_docs_audit_subdir(self, tmp_path: Path) -> None:
        report = self._base_report()
        json_out = write_json_report(report, tmp_path)
        md_out = write_md_report(report, tmp_path)
        assert json_out.parent.name == "audit"
        assert md_out.parent.name == "audit"

    def test_report_dir_created_if_missing(self, tmp_path: Path) -> None:
        report = self._base_report()
        # tmp_path/docs/audit should not exist yet
        assert not (tmp_path / "docs" / "audit").exists()
        write_json_report(report, tmp_path)
        assert (tmp_path / "docs" / "audit").exists()


# ---------------------------------------------------------------------------
# 7. Excluded directories not scanned as dependency sources
# ---------------------------------------------------------------------------


class TestExcludedDirs:
    """Documented excluded directories must not be used as dep sources."""

    def test_ecc_source_excluded(self) -> None:
        assert ".ecc-source" in EXCLUDED_DIRS

    def test_venv_excluded(self) -> None:
        assert ".venv" in EXCLUDED_DIRS

    def test_git_excluded(self) -> None:
        assert ".git" in EXCLUDED_DIRS

    def test_artifacts_excluded(self) -> None:
        assert "artifacts" in EXCLUDED_DIRS

    def test_docs_audit_excluded(self) -> None:
        assert "docs/audit" in EXCLUDED_DIRS

    def test_node_dep_files_do_not_include_excluded_dirs(self) -> None:
        """NODE_DEP_FILES should only list filenames, not paths in excluded dirs."""
        for f in NODE_DEP_FILES:
            for excl in EXCLUDED_DIRS:
                assert not f.startswith(excl), f"{f} starts with excluded dir {excl}"


# ---------------------------------------------------------------------------
# 8. No wallet/signing/submission behaviour in audit script
# ---------------------------------------------------------------------------


class TestNoWalletBehaviour:
    """Verify the audit script contains no wallet/signing/submission code."""

    SCRIPT_PATH = SCRIPTS_DIR / "dependency_audit.py"

    FORBIDDEN_PATTERNS = [
        "from_seed",
        "Wallet.create",
        "Wallet.from_seed",
        "submitAndWait",
        "autofill",
        "private_key =",
        "familySeed",
        "mnemonic",
        "xrpl.wallet",
    ]

    def test_no_forbidden_patterns_in_audit_script(self) -> None:
        assert self.SCRIPT_PATH.exists(), "dependency_audit.py must exist"
        source = self.SCRIPT_PATH.read_text(encoding="utf-8")
        violations = [p for p in self.FORBIDDEN_PATTERNS if p in source]
        assert not violations, f"Forbidden patterns found in dependency_audit.py: {violations}"

    def test_script_does_not_import_xrpl_wallet(self) -> None:
        source = self.SCRIPT_PATH.read_text(encoding="utf-8")
        assert "from xrpl.wallet" not in source
        assert "import xrpl.wallet" not in source

    def test_script_does_not_make_network_calls(self) -> None:
        source = self.SCRIPT_PATH.read_text(encoding="utf-8")
        # Should not import socket/requests/websockets for network
        assert "import requests" not in source
        assert "import websocket" not in source
        assert "import socket\n" not in source
        # httpx or aiohttp would be suspicious too
        assert "import httpx" not in source
        assert "import aiohttp" not in source


# ---------------------------------------------------------------------------
# 9. python_dep_files check
# ---------------------------------------------------------------------------


class TestPythonDepFiles:
    """Tests for Python dependency file inventory."""

    def test_pyproject_toml_found_in_repo(self) -> None:
        result = check_python_dep_files(REPO_ROOT)
        assert "pyproject.toml" in result["files_found"]

    def test_returns_info_status(self) -> None:
        result = check_python_dep_files(REPO_ROOT)
        assert result["status"] == "info"
        assert result["passed"] is True

    def test_empty_repo_returns_info(self, tmp_path: Path) -> None:
        result = check_python_dep_files(tmp_path)
        assert result["status"] == "info"
        assert result["passed"] is True
        assert result["files_found"] == []
