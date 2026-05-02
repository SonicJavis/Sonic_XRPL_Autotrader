#!/usr/bin/env python3
"""Audit Validator
Automatically runs the repository audit steps and produces machine‑readable JSON
and a human‑readable Markdown summary.
The script is read‑only – it never modifies repository files (except the
generated report artifacts) and does not perform any network calls.
"""
import json, subprocess, sys, os, shlex
from pathlib import Path

def run_cmd(cmd, cwd=None):
    """Run a shell command, return dict with exit code, stdout, stderr."""
    result = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True)
    return {
        "cmd": cmd,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }

def check_output_contains(output, patterns):
    """Return True if any pattern appears in output (case‑insensitive)."""
    low = output.lower()
    return any(p.lower() in low for p in patterns)

def main():
    repo_root = Path(__file__).resolve().parents[1]
    steps = {}
    # 1. Git status
    steps["git_status"] = run_cmd("git status", cwd=repo_root)
    # 2. Branch list
    steps["git_branch_a"] = run_cmd("git branch -a", cwd=repo_root)
    # 3. Recent log (last 5 commits)
    steps["git_log"] = run_cmd("git log -5 --oneline --decorate", cwd=repo_root)
    # 4. Safety grep
    steps["safety_grep"] = run_cmd(".venv\\Scripts\\python.exe scripts\\safety_grep.py", cwd=repo_root)
    # 5. Pytest
    steps["pytest"] = run_cmd(".venv\\Scripts\\python.exe -m pytest", cwd=repo_root)
    # 6. Import smoke
    import_cmd = (
        ".venv\\Scripts\\python.exe -c \"import execution_prototype.reconciliation, "
        "execution_prototype.calibration_recommendations, execution_prototype.drift_intelligence, "
        "execution_prototype.discovery, execution_prototype.paper_operator, "
        "execution_prototype.paper_review, execution_prototype.pipeline, execution_prototype.strategy, "
        "execution_prototype.strategy_performance, execution_prototype.risk_governor, "
        "execution_prototype.campaign_runner, execution_prototype.market_fixtures, "
        "execution_prototype.data_adapters, execution_prototype.backtest_datasets, "
        "execution_prototype.quality; print('ALL_IMPORTS_OK')\""
    )
    steps["import_smoke"] = run_cmd(import_cmd, cwd=repo_root)
    # 7. CLI help checks (list of modules)
    cli_modules = [
        "execution_prototype.reconciliation.cli",
        "execution_prototype.calibration_recommendations.cli",
        "execution_prototype.drift_intelligence.cli",
        "execution_prototype.discovery.cli",
        "execution_prototype.paper_operator.cli",
        "execution_prototype.paper_review.cli",
        "execution_prototype.pipeline.cli",
        "execution_prototype.strategy_performance.cli",
        "execution_prototype.risk_governor.cli",
        "execution_prototype.campaign_runner.cli",
        "execution_prototype.market_fixtures.cli",
        "execution_prototype.data_adapters.cli",
        "execution_prototype.backtest_datasets.cli",
    ]
    for mod in cli_modules:
        key = f"cli_{mod.split('.')[-2]}"
        cmd = f".venv\\Scripts\\python.exe -m {mod} --help"
        steps[key] = run_cmd(cmd, cwd=repo_root)
    # 8. Docs consistency checks
    required_truths = {
        "SYSTEM_STATE.md": ["Phase 42", "paper-only", "Live Trading: 0/100", "no wallet", "no signing", "no submission"],
        "LIVE_TRADING_READINESS_GATES.md": ["Live Trading: 0/100"],
        "README.md": ["Phase 42", "paper-only", "no wallet", "no signing"],
        "PAPER_AUTONOMY_TEST_PLAN.md": ["offline", "paper"]
    }
    for doc, truths in required_truths.items():
        doc_path = repo_root / ("docs" if doc != "README.md" else "") / doc
        if doc_path.is_file():
            content = doc_path.read_text()
            missing = [t for t in truths if not check_output_contains(content, [t])]
            steps[f"doc_{doc}"] = {"found": True, "missing": missing}
        else:
            steps[f"doc_{doc}"] = {"found": False, "missing": truths}
    # Assemble report
    report = {"steps": steps}
    # Write JSON report
    json_path = Path.cwd() / "artifacts" / "audit_validator_report.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2))
    # Write markdown summary
    md_lines = ["# Audit Validator Summary", ""]
    for name, data in steps.items():
        md_lines.append(f"## {name}")
        if isinstance(data, dict) and "returncode" in data:
            status = "PASS" if data["returncode"] == 0 else "FAIL"
            md_lines.append(f"**Status:** {status}")
            md_lines.append(f"**Command:** `{data['cmd']}`")
            md_lines.append(f"**Stdout (first 200 chars):** `{data['stdout'][:200]}`")
            if data['stderr']:
                md_lines.append(f"**Stderr:** `{data['stderr'][:200]}`")
        else:
            md_lines.append(str(data))
        md_lines.append("")
    md_path = Path.cwd() / "artifacts" / "audit_validator_summary.md"
    md_path.write_text("\n".join(md_lines))
    # Exit code 0 if all critical steps passed
    critical = ["git_status", "git_branch_a", "safety_grep", "pytest", "import_smoke"] + [f"cli_{m.split('.')[-2]}" for m in cli_modules]
    exit_code = 0
    for key in critical:
        step = steps.get(key, {})
        if isinstance(step, dict) and step.get("returncode", 1) != 0:
            exit_code = 1
            break
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
