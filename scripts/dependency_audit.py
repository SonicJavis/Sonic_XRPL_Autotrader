"""Phase 48 — Dependency Audit Script.

Read-only audit of Python and Node dependency files.

Checks:
  1. pip check — verify no broken requirements
  2. pip-audit — check for known vulnerabilities (warning if unavailable/network issues)
  3. xrpl.js compromised version detection in Node dependency files
  4. Writes JSON and Markdown reports to docs/audit/

Exit codes:
  0 = pass
  1 = clear dependency/security failure
  2 = warning-only (pip-audit unavailable/network unavailable, no known bad detected)

Usage:
  python scripts/dependency_audit.py
  python scripts/dependency_audit.py --write-report
  python scripts/dependency_audit.py --write-report --strict
  python scripts/dependency_audit.py --skip-pip-audit
  python scripts/dependency_audit.py --json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COMPROMISED_XRPL_JS_VERSIONS = {
    "4.2.1", "4.2.2", "4.2.3", "4.2.4", "2.14.2"
}

# 4.x: safe from 4.2.5+, 2.x: safe from 2.14.3+
SAFE_XRPL_JS_PATCHED = {"4.2.5"}

# Node dependency files to inspect
NODE_DEP_FILES = [
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
]

# Python dependency files to document (existence check only, no parsing)
PYTHON_DEP_FILES = [
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "poetry.lock",
    "Pipfile",
    "Pipfile.lock",
]

# Directories to never scan as dependency sources
EXCLUDED_DIRS = {".ecc-source", ".venv", ".git", "artifacts", "docs/audit", "node_modules"}

REPORT_DIR_REL = "docs/audit"
JSON_REPORT_NAME = "latest_dependency_audit.json"
MD_REPORT_NAME = "latest_dependency_audit.md"

# ---------------------------------------------------------------------------
# Repo-root detection
# ---------------------------------------------------------------------------


def _find_repo_root() -> Path:
    """Locate the repository root (directory containing pyproject.toml)."""
    candidate = Path(__file__).resolve().parent.parent
    if (candidate / "pyproject.toml").exists():
        return candidate
    # Fallback: walk up from cwd
    cwd = Path.cwd()
    for p in [cwd, *cwd.parents]:
        if (p / "pyproject.toml").exists():
            return p
    return cwd


REPO_ROOT = _find_repo_root()

# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def check_pip(python_exe: str | None = None) -> dict:
    """Run `pip check` to verify no broken requirements."""
    exe = python_exe or sys.executable
    try:
        result = subprocess.run(
            [exe, "-m", "pip", "check"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        passed = result.returncode == 0
        output = (result.stdout + result.stderr).strip()
        return {
            "status": "pass" if passed else "fail",
            "passed": passed,
            "message": output or "No broken requirements found.",
            "exit_code": result.returncode,
        }
    except Exception as exc:
        return {
            "status": "fail",
            "passed": False,
            "message": f"pip check failed to run: {exc}",
            "exit_code": -1,
        }


def check_pip_audit(python_exe: str | None = None, skip: bool = False) -> dict:
    """Run pip-audit to check for known vulnerabilities.

    Returns warning (not fail) if pip-audit is unavailable or network is down.
    Returns fail only if known vulnerabilities are positively found.
    """
    if skip:
        return {
            "status": "skipped",
            "passed": True,
            "message": "pip-audit skipped by --skip-pip-audit flag.",
            "vulnerabilities": [],
        }

    exe = python_exe or sys.executable

    # Check if pip_audit module is importable
    probe = subprocess.run(
        [exe, "-c", "import pip_audit"],
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0:
        return {
            "status": "warning",
            "passed": True,
            "message": (
                "pip-audit is not installed. Install with: pip install pip-audit\n"
                "Add pip-audit to [project.optional-dependencies].dev in pyproject.toml."
            ),
            "vulnerabilities": [],
        }

    try:
        result = subprocess.run(
            [exe, "-m", "pip_audit", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        # pip-audit exits 0 if no vulnerabilities; non-zero if vulnerabilities found
        # It may also fail if the network/DB is unavailable
        if result.returncode == 0:
            vulns = _parse_pip_audit_json(stdout)
            return {
                "status": "pass",
                "passed": True,
                "message": "pip-audit: no known vulnerabilities found.",
                "vulnerabilities": vulns,
            }

        # Try to parse JSON to distinguish real vulns from network/DB failures
        vulns = _parse_pip_audit_json(stdout)
        if vulns:
            # Real vulnerabilities found
            vuln_summary = "; ".join(
                f"{v.get('name', '?')}@{v.get('version', '?')}: {v.get('id', '?')}"
                for v in vulns[:5]
            )
            return {
                "status": "fail",
                "passed": False,
                "message": f"pip-audit found {len(vulns)} vulnerability(ies): {vuln_summary}",
                "vulnerabilities": vulns,
            }

        # Non-zero exit but no parsed vulns — likely network/DB issue
        hint = (stderr or stdout)[:300]
        return {
            "status": "warning",
            "passed": True,
            "message": (
                f"pip-audit exited {result.returncode} but no vulnerabilities parsed. "
                f"Possible network/DB issue: {hint}"
            ),
            "vulnerabilities": [],
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "warning",
            "passed": True,
            "message": "pip-audit timed out (120s). Vulnerability DB may be unreachable.",
            "vulnerabilities": [],
        }
    except Exception as exc:
        return {
            "status": "warning",
            "passed": True,
            "message": f"pip-audit could not run: {exc}",
            "vulnerabilities": [],
        }


def _parse_pip_audit_json(text: str) -> list[dict]:
    """Parse pip-audit JSON output into a list of vulnerability dicts."""
    if not text:
        return []
    try:
        data = json.loads(text)
        # pip-audit JSON format: {"dependencies": [{"name": ..., "version": ..., "vulns": [...]}]}
        vulns = []
        for dep in data.get("dependencies", []):
            for v in dep.get("vulns", []):
                vulns.append({
                    "name": dep.get("name", ""),
                    "version": dep.get("version", ""),
                    "id": v.get("id", ""),
                    "description": v.get("description", "")[:200],
                })
        return vulns
    except Exception:
        return []


def check_node_dependencies(repo_root: Path) -> dict:
    """Check Node dependency files for compromised xrpl.js versions."""
    found_any_node_file = False
    findings = []
    warnings = []

    # Check package.json
    pkg_json_path = repo_root / "package.json"
    if pkg_json_path.exists():
        found_any_node_file = True
        result = _check_package_json(pkg_json_path)
        findings.extend(result["findings"])
        warnings.extend(result["warnings"])

    # Check package-lock.json
    lock_path = repo_root / "package-lock.json"
    if lock_path.exists():
        found_any_node_file = True
        result = _check_lockfile_text(lock_path, "package-lock.json")
        findings.extend(result["findings"])

    # Check pnpm-lock.yaml
    pnpm_path = repo_root / "pnpm-lock.yaml"
    if pnpm_path.exists():
        found_any_node_file = True
        result = _check_lockfile_text(pnpm_path, "pnpm-lock.yaml")
        findings.extend(result["findings"])

    if not found_any_node_file:
        return {
            "status": "not_applicable",
            "passed": True,
            "message": "No Node dependency files found — xrpl.js audit not applicable.",
            "findings": [],
            "warnings": [],
        }

    compromised = [f for f in findings if f["severity"] == "critical"]
    if compromised:
        msgs = "; ".join(f["message"] for f in compromised)
        return {
            "status": "fail",
            "passed": False,
            "message": f"COMPROMISED xrpl.js version(s) found: {msgs}",
            "findings": findings,
            "warnings": warnings,
        }

    msg = "No compromised xrpl.js versions found in Node dependency files."
    if findings:
        msg += " " + "; ".join(f["message"] for f in findings)
    return {
        "status": "pass",
        "passed": True,
        "message": msg,
        "findings": findings,
        "warnings": warnings,
    }


def _check_package_json(path: Path) -> dict:
    """Parse package.json for xrpl version entries."""
    findings = []
    warnings = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        for dep_section in ("dependencies", "devDependencies", "peerDependencies"):
            deps = data.get(dep_section, {})
            if "xrpl" in deps:
                raw_ver = deps["xrpl"]
                version = raw_ver.lstrip("^~>=v")
                if version in COMPROMISED_XRPL_JS_VERSIONS:
                    findings.append({
                        "file": "package.json",
                        "section": dep_section,
                        "package": "xrpl",
                        "version": version,
                        "severity": "critical",
                        "message": (
                            f"COMPROMISED xrpl@{version} in {dep_section} "
                            f"(package.json). Upgrade to 4.2.5+ or 2.14.3+."
                        ),
                    })
                else:
                    findings.append({
                        "file": "package.json",
                        "section": dep_section,
                        "package": "xrpl",
                        "version": version,
                        "severity": "info",
                        "message": f"xrpl@{version} in {dep_section} (package.json) — not in compromised list.",
                    })
    except Exception as exc:
        warnings.append(f"Could not parse package.json: {exc}")
    return {"findings": findings, "warnings": warnings}


def _check_lockfile_text(path: Path, label: str) -> dict:
    """Scan lockfile text for compromised xrpl.js version strings."""
    findings = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for v in COMPROMISED_XRPL_JS_VERSIONS:
            # Match version string in common lockfile formats
            patterns = [f'"xrpl@{v}"', f'"version": "{v}"', f"xrpl@{v}", f"'xrpl@{v}'"]
            if any(p in text for p in patterns):
                findings.append({
                    "file": label,
                    "package": "xrpl",
                    "version": v,
                    "severity": "critical",
                    "message": (
                        f"COMPROMISED xrpl@{v} found in {label}. "
                        "Upgrade to 4.2.5+ or 2.14.3+ and regenerate lockfile."
                    ),
                })
    except Exception as exc:
        findings.append({
            "file": label,
            "package": "unknown",
            "version": "unknown",
            "severity": "warning",
            "message": f"Could not read {label}: {exc}",
        })
    return {"findings": findings}


def check_python_dep_files(repo_root: Path) -> dict:
    """Inventory Python dependency files (existence check only)."""
    found = []
    for rel in PYTHON_DEP_FILES:
        p = repo_root / rel
        if p.exists():
            found.append(rel)
    return {
        "status": "info",
        "passed": True,
        "message": f"Python dependency files found: {found}" if found else "No standard Python dep files (only pyproject.toml).",
        "files_found": found,
    }


# ---------------------------------------------------------------------------
# Report building
# ---------------------------------------------------------------------------


def build_report(
    pip_check_result: dict,
    pip_audit_result: dict,
    node_result: dict,
    python_files_result: dict,
) -> dict:
    """Assemble the full audit report dict."""
    findings = []
    warnings = []

    # Collect findings
    if not pip_check_result["passed"]:
        findings.append({"source": "pip_check", "message": pip_check_result["message"]})
    if not pip_audit_result["passed"]:
        findings.append({"source": "pip_audit", "message": pip_audit_result["message"]})
    for w in node_result.get("warnings", []):
        warnings.append(w)
    if not node_result["passed"]:
        for f in node_result.get("findings", []):
            if f.get("severity") == "critical":
                findings.append({"source": "xrpl_js", "message": f["message"]})
    for f in node_result.get("findings", []):
        if f.get("severity") not in ("critical",):
            warnings.append(f["message"])
    if pip_audit_result["status"] == "warning":
        warnings.append(pip_audit_result["message"])

    # Overall status
    hard_fail = (
        not pip_check_result["passed"]
        or pip_audit_result["status"] == "fail"
        or node_result["status"] == "fail"
    )
    warn_only = (
        not hard_fail
        and (
            pip_audit_result["status"] in ("warning", "skipped")
            or any(f.get("severity") == "warning" for f in node_result.get("findings", []))
        )
    )

    if hard_fail:
        overall_status = "fail"
    elif warn_only:
        overall_status = "warning"
    else:
        overall_status = "pass"

    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "phase": "48",
        "overall_status": overall_status,
        "python_dependency_check": pip_check_result,
        "pip_audit": pip_audit_result,
        "node_dependency_check": node_result,
        "python_dependency_files": python_files_result,
        "findings": findings,
        "warnings": warnings,
    }


def write_json_report(report: dict, repo_root: Path) -> Path:
    """Write JSON report to docs/audit/latest_dependency_audit.json."""
    out_dir = repo_root / REPORT_DIR_REL
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / JSON_REPORT_NAME
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return out_path


def write_md_report(report: dict, repo_root: Path) -> Path:
    """Write Markdown report to docs/audit/latest_dependency_audit.md."""
    out_dir = repo_root / REPORT_DIR_REL
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / MD_REPORT_NAME

    status_icon = {"pass": "PASS", "warning": "WARN", "fail": "FAIL"}.get(report["overall_status"], "UNKNOWN")

    lines = [
        "# Dependency Audit Report (Phase 48)",
        "",
        f"**Generated**: {report['generated_at']}",
        f"**Overall Status**: {status_icon} {report['overall_status'].upper()}",
        "",
        "---",
        "",
        "## Python Dependency Checks",
        "",
    ]

    pc = report["python_dependency_check"]
    pc_icon = "PASS" if pc["passed"] else "FAIL"
    lines += [
        f"### pip check: {pc_icon}",
        f"```",
        pc["message"],
        "```",
        "",
    ]

    pa = report["pip_audit"]
    pa_icon = {"pass": "PASS", "warning": "WARN", "fail": "FAIL", "skipped": "SKIP"}.get(pa["status"], "UNKNOWN")
    lines += [
        f"### pip-audit: {pa_icon} ({pa['status']})",
        f"```",
        pa["message"],
        "```",
    ]
    if pa.get("vulnerabilities"):
        lines.append("")
        lines.append("**Vulnerabilities Found:**")
        for v in pa["vulnerabilities"]:
            lines.append(f"- `{v.get('name')}@{v.get('version')}`: {v.get('id')} — {v.get('description', '')}")
    lines.append("")

    nd = report["node_dependency_check"]
    nd_icon = {"pass": "PASS", "warning": "WARN", "fail": "FAIL", "not_applicable": "INFO"}.get(nd["status"], "UNKNOWN")
    lines += [
        "## Node / xrpl.js Checks",
        "",
        f"### xrpl.js audit: {nd_icon} ({nd['status']})",
        f"```",
        nd["message"],
        "```",
    ]
    if nd.get("findings"):
        lines.append("")
        lines.append("**Findings:**")
        for f in nd["findings"]:
            sev_icon = "CRITICAL" if f.get("severity") == "critical" else "INFO"
            lines.append(f"- {sev_icon} {f['message']}")
    lines.append("")

    if report["findings"]:
        lines += ["## Security Findings", ""]
        for f in report["findings"]:
            lines.append(f"- FAIL **{f.get('source', 'unknown')}**: {f.get('message', '')}")
        lines.append("")

    if report["warnings"]:
        lines += ["## Warnings", ""]
        for w in report["warnings"]:
            lines.append(f"- WARN {w}")
        lines.append("")

    lines += [
        "---",
        "",
        "## Safety Statement",
        "",
        "- No wallet, seed, or private key is read or processed.",
        "- No XRPL network calls are made.",
        "- No transaction signing or submission is performed.",
        "- No trading behaviour is changed by this audit.",
        "- This script is read-only except for writing report files to `docs/audit/`.",
    ]

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
# Console output
# ---------------------------------------------------------------------------


def print_summary(report: dict) -> None:
    """Print a human-readable summary to stdout."""
    status = report["overall_status"].upper()
    sep = "=" * 60
    print(sep)
    print(f"  DEPENDENCY AUDIT — Phase 48")
    print(f"  {report['generated_at']}")
    print(sep)

    pc = report["python_dependency_check"]
    pc_icon = "PASS" if pc["passed"] else "FAIL"
    print(f"\n[pip check]       {pc_icon}: {pc['message'][:80]}")

    pa = report["pip_audit"]
    pa_label = pa["status"].upper()
    print(f"[pip-audit]       {pa_label}: {pa['message'][:80]}")

    nd = report["node_dependency_check"]
    nd_label = nd["status"].upper()
    print(f"[xrpl.js]         {nd_label}: {nd['message'][:80]}")

    if report["findings"]:
        print("\n--- SECURITY FINDINGS ---")
        for f in report["findings"]:
            print(f"  FAIL {f.get('source')}: {f.get('message')}")

    if report["warnings"]:
        print("\n--- WARNINGS ---")
        for w in report["warnings"]:
            print(f"  WARN {w}")

    print(f"\n{sep}")
    print(f"  OVERALL: {status}")
    print(sep)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Run the dependency audit and return exit code."""
    parser = argparse.ArgumentParser(
        description="Phase 48 Dependency Audit — read-only supply-chain check."
    )
    parser.add_argument(
        "--write-report",
        action="store_true",
        help="Write JSON and Markdown reports to docs/audit/",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full JSON report to stdout (in addition to summary).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures (exit 1 instead of 2 for warning-only runs).",
    )
    parser.add_argument(
        "--skip-pip-audit",
        action="store_true",
        help="Skip pip-audit check (useful in restricted/offline environments).",
    )
    args = parser.parse_args(argv)

    repo_root = REPO_ROOT

    # Run checks
    print("Running pip check ...")
    pip_result = check_pip()

    print("Running pip-audit ...")
    pa_result = check_pip_audit(skip=args.skip_pip_audit)

    print("Checking Node dependency files ...")
    node_result = check_node_dependencies(repo_root)

    python_files = check_python_dep_files(repo_root)

    # Assemble report
    report = build_report(pip_result, pa_result, node_result, python_files)

    # Output
    print_summary(report)

    if args.json:
        print("\n--- JSON REPORT ---")
        print(json.dumps(report, indent=2))

    if args.write_report:
        json_path = write_json_report(report, repo_root)
        md_path = write_md_report(report, repo_root)
        print(f"\nReports written:")
        print(f"  JSON: {json_path}")
        print(f"  MD:   {md_path}")

    # Exit code
    overall = report["overall_status"]
    if overall == "fail":
        return 1
    if overall == "warning" and args.strict:
        return 1
    if overall == "warning":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
