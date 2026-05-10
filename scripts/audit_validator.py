"""Phase 42.2+ – Audit Validator.

Runs a suite of repo-wide integrity and safety checks and writes a
machine-readable JSON report to artifacts/audit_validator_report.json.

Checks performed:
  1. Branch hygiene  – git status / git log
  2. Safety grep     – delegates to scripts/safety_grep.py
  3. Import smoke    – tries to import every package under execution_prototype
  4. CLI help        – calls -h on every execution_prototype/**/cli.py entry-point
  5. Doc disclosures – verifies migration/safety disclosures in docs and README
"""

from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure the repo root is on sys.path so execution_prototype is importable
# regardless of the directory the script was invoked from.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ARTIFACTS_DIR = REPO_ROOT / "artifacts"

REQUIRED_SAFETY_STRINGS = {
    "docs/SYSTEM_STATE.md": [
        "paper-only",
        "0/100",
        "Fail-Closed",
        "canonical-path decision remains intentionally unresolved",
    ],
    "README.md": [
        "paper",
        "No wallet",
        "Canonical Path Decision: Pending",
        "No new features may be added to `app/` or `execution_prototype/` until the",
        "required safety conformance tests pass",
    ],
    "docs/V2_ARCHITECTURE.md": [
        "## Canonical Path Decision: Pending",
        "### Legacy Surface Freeze (Pending Decision)",
    ],
    "docs/SAFETY_MODEL.md": [
        "## Legacy Freeze Policy (PR 3)",
        "required safety conformance tests pass",
    ],
}

# Sub-packages of execution_prototype to smoke-import (directory-based discovery
# is done at runtime, but we list the top-level sub-packages explicitly so the
# test is deterministic and not affected by transient generated artefacts).
PROTOTYPE_PACKAGES = [
    "execution_prototype",
    "execution_prototype.reconciliation",
    "execution_prototype.calibration_recommendations",
    "execution_prototype.drift_intelligence",
    "execution_prototype.discovery",
    "execution_prototype.paper_review",
    "execution_prototype.paper_operator",
    "execution_prototype.strategy_performance",
    "execution_prototype.risk_governor",
    "execution_prototype.campaign_runner",
    "execution_prototype.market_fixtures",
    "execution_prototype.data_adapters",
    "execution_prototype.backtest_datasets",
    "execution_prototype.pipeline",
    "execution_prototype.quality",
    "execution_prototype.strategy",
    "execution_prototype.dataset_strategy_tournament",
    "execution_prototype.walk_forward_replay",
]

# Mapping of human-readable label → dotted module path for every cli.py that
# exposes a main() function.  The module is called with ["-h"] to verify the
# argparse setup is intact.
CLI_MODULES: dict[str, str] = {
    "execution_prototype (root)": "execution_prototype.cli",
    "reconciliation": "execution_prototype.reconciliation.cli",
    "calibration_recommendations": "execution_prototype.calibration_recommendations.cli",
    "drift_intelligence": "execution_prototype.drift_intelligence.cli",
    "discovery": "execution_prototype.discovery.cli",
    "paper_review": "execution_prototype.paper_review.cli",
    "strategy_performance": "execution_prototype.strategy_performance.cli",
    "risk_governor": "execution_prototype.risk_governor.cli",
    "campaign_runner": "execution_prototype.campaign_runner.cli",
    "market_fixtures": "execution_prototype.market_fixtures.cli",
    "data_adapters": "execution_prototype.data_adapters.cli",
    "backtest_datasets": "execution_prototype.backtest_datasets.cli",
    "pipeline": "execution_prototype.pipeline.cli",
    "dataset_strategy_tournament": "execution_prototype.dataset_strategy_tournament.cli",
    "walk_forward_replay": "execution_prototype.walk_forward_replay.cli",
}

# ---------------------------------------------------------------------------
# Individual check functions
# ---------------------------------------------------------------------------


def check_branch_hygiene() -> dict:
    """Return git status and recent log for manual review."""
    results: dict[str, object] = {"passed": True, "details": {}}
    try:
        status = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        log = subprocess.run(
            ["git", "log", "--oneline", "-10"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        results["details"]["git_status"] = status.stdout.strip() or "(clean)"
        results["details"]["git_log"] = log.stdout.strip()
        results["details"]["uncommitted_files"] = len(
            [l for l in status.stdout.splitlines() if l.strip()]
        )
    except Exception as exc:  # noqa: BLE001
        results["passed"] = False
        results["details"]["error"] = str(exc)
    return results


def _subprocess_env() -> dict[str, str]:
    """Return an environment with REPO_ROOT prepended to PYTHONPATH."""
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(REPO_ROOT) + (os.pathsep + existing if existing else "")
    return env


def check_safety_grep() -> dict:
    """Run scripts/safety_grep.py and capture its exit code + output."""
    safety_script = REPO_ROOT / "scripts" / "safety_grep.py"
    result = subprocess.run(
        [sys.executable, str(safety_script)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env=_subprocess_env(),
    )
    passed = result.returncode == 0
    return {
        "passed": passed,
        "details": {
            "exit_code": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        },
    }


def check_import_smoke() -> dict:
    """Try to import every package in PROTOTYPE_PACKAGES."""
    failures: list[str] = []
    successes: list[str] = []

    for module_name in PROTOTYPE_PACKAGES:
        try:
            importlib.import_module(module_name)
            successes.append(module_name)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{module_name}: {exc}")

    return {
        "passed": len(failures) == 0,
        "details": {
            "total": len(PROTOTYPE_PACKAGES),
            "success_count": len(successes),
            "failure_count": len(failures),
            "failures": failures,
        },
    }


def check_cli_help() -> dict:
    """Call each CLI module with -h and verify it exits with code 0."""
    failures: list[str] = []
    successes: list[str] = []

    for label, module_path in CLI_MODULES.items():
        result = subprocess.run(
            [sys.executable, "-m", module_path, "-h"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            env=_subprocess_env(),
        )
        if result.returncode == 0:
            successes.append(label)
        else:
            failures.append(
                f"{label} ({module_path}): exit={result.returncode} "
                f"stderr={result.stderr.strip()[:200]}"
            )

    return {
        "passed": len(failures) == 0,
        "details": {
            "total": len(CLI_MODULES),
            "success_count": len(successes),
            "failure_count": len(failures),
            "failures": failures,
        },
    }


def check_doc_disclosures() -> dict:
    """Verify key migration/safety strings appear in required docs."""
    failures: list[str] = []
    checked: list[dict] = []

    for rel_path, required_strings in REQUIRED_SAFETY_STRINGS.items():
        doc_path = REPO_ROOT / rel_path
        if not doc_path.exists():
            failures.append(f"{rel_path}: file not found")
            continue
        content = doc_path.read_text(encoding="utf-8", errors="ignore")
        for s in required_strings:
            if s.lower() not in content.lower():
                failures.append(f"{rel_path}: missing required string '{s}'")
            else:
                checked.append({"file": rel_path, "string": s, "found": True})

    return {
        "passed": len(failures) == 0,
        "details": {
            "checked": checked,
            "failures": failures,
        },
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    print("=== Phase 42.2+ Audit Validator ===")
    print(f"Repo root : {REPO_ROOT}")
    print(f"Timestamp : {datetime.now(timezone.utc).isoformat()}")
    print()

    checks: dict[str, dict] = {}

    print("[1/5] Branch hygiene ...")
    checks["branch_hygiene"] = check_branch_hygiene()
    _print_status(checks["branch_hygiene"])

    print("[2/5] Safety grep ...")
    checks["safety_grep"] = check_safety_grep()
    _print_status(checks["safety_grep"])

    print("[3/5] Import smoke test ...")
    checks["import_smoke"] = check_import_smoke()
    _print_status(checks["import_smoke"])

    print("[4/5] CLI help test ...")
    checks["cli_help"] = check_cli_help()
    _print_status(checks["cli_help"])

    print("[5/5] Documentation disclosures ...")
    checks["doc_disclosures"] = check_doc_disclosures()
    _print_status(checks["doc_disclosures"])

    overall_passed = all(c["passed"] for c in checks.values())

    report = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "phase": "42.2+",
        "overall_passed": overall_passed,
        "checks": checks,
    }

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = ARTIFACTS_DIR / "audit_validator_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    print()
    print(f"Report written to: {report_path}")
    if overall_passed:
        print("AUDIT PASSED – all checks green.")
    else:
        failed_names = [name for name, c in checks.items() if not c["passed"]]
        print(f"AUDIT FAILED – failing checks: {', '.join(failed_names)}")

    return 0 if overall_passed else 1


def _print_status(result: dict) -> None:
    status = "PASS" if result["passed"] else "FAIL"
    print(f"  -> {status}")
    if not result["passed"]:
        details = result.get("details", {})
        for key in ("failures", "error", "stderr"):
            value = details.get(key)
            if value:
                if isinstance(value, list):
                    for item in value:
                        print(f"     • {item}")
                else:
                    print(f"     • {value}")
    print()


if __name__ == "__main__":
    raise SystemExit(main())
